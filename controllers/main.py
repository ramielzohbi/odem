# controllers/main.py
from odoo import http
from odoo.http import request
import json

class EventController(http.Controller):
    @http.route(['/register/<string:registration_url>'], type='http', auth="public", website=True)
    def register_event(self, registration_url, **kwargs):
        # Update the model name to match our new naming
        category = request.env['event.mgmt.category'].sudo().search([
            ('registration_url', '=', f"/register/{registration_url}")
        ], limit=1)
        
        if not category:
            return request.not_found()
            
        values = {
            'category': category,
            'event': category.event_id,
        }
        return request.render("event_management.registration_form", values)
    
    @http.route(['/registration/submit'], type='http', auth="public", website=True, methods=['POST'], csrf=True)
    def submit_registration(self, **post):
        category_id = int(post.get('category_id', 0))
        category = request.env['event.mgmt.category'].sudo().browse(category_id)
        
        if not category:
            return json.dumps({'error': 'Invalid category'})
            
        vals = {
            'event_id': category.event_id.id,
            'category_id': category.id,
            'first_name': post.get('first_name'),
            'last_name': post.get('last_name'),
            'email': post.get('email'),
            'phone': post.get('phone'),
            'company': post.get('company'),
            'job_title': post.get('job_title'),
            'state': 'draft'
        }
        
        try:
            # Update the model name to match our new naming
            registration = request.env['event.mgmt.registration'].sudo().create(vals)
            return request.render("event_management.registration_success", {
                'registration': registration,
            })
        except Exception as e:
            return json.dumps({'error': str(e)})
    
    @http.route(['/registration/check/<string:registration_number>'], type='http', auth="public", website=True)
    def check_registration(self, registration_number):
        # Update the model name to match our new naming
        registration = request.env['event.mgmt.registration'].sudo().search([
            ('name', '=', registration_number)
        ], limit=1)
        
        if not registration:
            return request.not_found()
            
        return request.render("event_management.registration_status", {
            'registration': registration,
        })