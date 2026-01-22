# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies
#
################################################################################
import requests
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = 'res.users'

    api_key = fields.Char(string='API KEY')
    token = fields.Char(string='Token')
    user_name = fields.Char(string='Trello Username')

    _sql_constraints = [
        ('api_key_uniq', 'unique(api_key)', 'API Key must be unique per User !'),
        ('username_uniq', 'unique(user_name)', 'Username must be unique per User !')
    ]

    # -------------------------------------------------------------------------
    # IMPORT
    # -------------------------------------------------------------------------

    def action_import(self):
        if not self.api_key or not self.token or not self.user_name:
            raise ValidationError(_("Please fill all fields."))

        query = {
            "key": self.api_key,
            "token": self.token,
        }
        headers = {"Accept": "application/json"}

        member_id = self.get_member_id(headers, self.user_name)

        for board in self.get_boards(headers, query, member_id):
            print(f">>> IMPORTING BOARD: {board['name']} ({board['id']})")
            self._delay_import(board, headers, query)

    def _delay_import(self, board, headers, query):
        # Project
        project = self.env['project.project'].sudo().search(
            [('trello_reference', '=', board['id'])],
            limit=1
        )
        if not project:
            project = self.env['project.project'].sudo().create({
                'name': board['name'],
                'description': board.get('desc'),
                'trello_reference': board['id']
            })

        # Lists → Stages
        for trello_list in self.get_list_on_board(headers, query, board['id']):
            stage = self.env['project.task.type'].search(
                [('name', '=', trello_list['name'])],
                limit=1
            )
            if not stage:
                stage = self.env['project.task.type'].sudo().create({
                    'name': trello_list['name']
                })

            if stage.id not in project.type_ids.ids:
                project.sudo().write({'type_ids': [(4, stage.id)]})

        # Cards → Tasks
        existing_refs = set(
            self.env['project.task'].search([]).mapped('trello_reference')
        )

        for card in self.get_cards(headers, query, board['id']):
            if card['id'] in existing_refs:
                continue

            trello_list = self.get_a_list(headers, query, card['idList'])
            stage = self.env['project.task.type'].search(
                [('name', '=', trello_list['name'])],
                limit=1
            )

            if not stage:
                stage = self.env['project.task.type'].sudo().create({
                    'name': trello_list['name']
                })

            self.env['project.task'].sudo().create({
                'name': card['name'],
                'project_id': project.id,
                'stage_id': stage.id,
                'trello_reference': card['id']
            })

    # -------------------------------------------------------------------------
    # EXPORT
    # -------------------------------------------------------------------------

    def action_export(self):
        if not self.api_key or not self.token or not self.user_name:
            raise ValidationError(_("Please fill all fields"))

        query = {
            "key": self.api_key,
            "token": self.token,
        }
        headers = {"Accept": "application/json"}

        for project in self.env['project.project'].search([]):
            if not project.trello_reference:
                board_id = self.create_board(headers, query, project.name)
                project.write({'trello_reference': board_id})

            lists_on_board = self.get_list_on_board(
                headers, query, project.trello_reference
            )

            for stage in project.type_ids:
                if stage.name not in [l['name'] for l in lists_on_board]:
                    self.create_list(
                        headers, query, project.trello_reference, stage.name
                    )

            for task in project.task_ids:
                if not task.trello_reference:
                    card = self.create_card(
                        headers,
                        query,
                        task.stage_reference,
                        task.name
                    )
                    task.write({'trello_reference': card['id']})

    # -------------------------------------------------------------------------
    # TRELLO API
    # -------------------------------------------------------------------------

    def get_member_id(self, headers, username):
        res = requests.get(
            f"https://api.trello.com/1/members/{username}",
            headers=headers,
            timeout=10
        )
        if res.status_code == 200:
            return res.json()['id']
        raise ValidationError(res.text)

    def get_boards(self, headers, query, member_id):
        query['filter'] = 'open'
        res = requests.get(
            f"https://api.trello.com/1/members/{member_id}/boards",
            headers=headers,
            params=query,
            timeout=10
        )
        if res.status_code == 200:
            return res.json()
        raise ValidationError(res.text)

    def get_cards(self, headers, query, board_id):
        res = requests.get(
            f"https://api.trello.com/1/boards/{board_id}/cards",
            headers=headers,
            params=query,
            timeout=10
        )
        if res.status_code == 200:
            return res.json()
        raise ValidationError(res.text)

    def get_list_on_board(self, headers, query, board_id):
        res = requests.get(
            f"https://api.trello.com/1/boards/{board_id}/lists",
            headers=headers,
            params=query,
            timeout=10
        )
        if res.status_code == 200:
            return res.json()
        raise ValidationError(res.text)

    def get_a_list(self, headers, query, list_id):
        res = requests.get(
            f"https://api.trello.com/1/lists/{list_id}",
            headers=headers,
            params=query,
            timeout=10
        )
        if res.status_code == 200:
            return res.json()
        raise ValidationError(res.text)

    def create_board(self, headers, query, name):
        query['name'] = name
        res = requests.post(
            "https://api.trello.com/1/boards/",
            headers=headers,
            params=query,
            timeout=10
        )
        if res.status_code == 200:
            return res.json()['id']
        raise ValidationError(res.text)

    def create_list(self, headers, query, board_id, name):
        query['name'] = name
        res = requests.post(
            f"https://api.trello.com/1/boards/{board_id}/lists",
            headers=headers,
            params=query,
            timeout=10
        )
        if res.status_code == 200:
            return res.json()
        raise ValidationError(res.text)

    def create_card(self, headers, query, list_id, name):
        query['idList'] = list_id
        query['name'] = name
        res = requests.post(
            "https://api.trello.com/1/cards",
            headers=headers,
            params=query,
            timeout=10
        )
        if res.status_code == 200:
            return res.json()
        raise ValidationError(res.text)
