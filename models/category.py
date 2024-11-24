from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import uuid
import json
import base64

class EventMgmtCategory(models.Model):
    _name = 'event.mgmt.category'
    _description = 'Event Category'
    _inherit = ['mail.thread']
    _order = 'sequence, id'

    name = fields.Char(string='Category Name', required=True, translate=True)
    code = fields.Char(string='Category Code', required=True)
    event_id = fields.Many2one('event.mgmt', string='Event', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(default=True)
    
    registration_url = fields.Char(string='Registration URL', readonly=True)
    max_registrations = fields.Integer(string='Maximum Registrations', default=0)
    
    registration_ids = fields.One2many('event.mgmt.registration', 'category_id', string='Registrations')
    current_registrations = fields.Integer(compute='_compute_registrations', store=True)
    
    # Email Templates
    confirmation_template_id = fields.Many2one('mail.template', string='Confirmation Email Template')
    approval_template_id = fields.Many2one('mail.template', string='Approval Email Template')
    rejection_template_id = fields.Many2one('mail.template', string='Rejection Email Template')
    
    # Form Configuration
    custom_fields = fields.One2many('event.mgmt.category.field', 'category_id', string='Custom Fields')
    
    # Settings
    requires_approval = fields.Boolean(string='Requires Approval', default=True)
    auto_approve = fields.Boolean(string='Auto Approve', default=False)

    # Validation Settings
    require_photo = fields.Boolean(string='Require Photo', default=True)
    require_id = fields.Boolean(string='Require ID', default=True)
    enable_ai_validation = fields.Boolean(string='Enable AI Validation', default=True)
    
    @api.model
    def create(self, vals):
        # Generate unique URL for registration using uuid
        if not vals.get('registration_url'):
            vals['registration_url'] = f"/register/{uuid.uuid4().hex}"
        return super(EventMgmtCategory, self).create(vals)
    
    @api.depends('registration_ids', 'registration_ids.state')
    def _compute_registrations(self):
        for category in self:
            category.current_registrations = len(category.registration_ids.filtered(
                lambda r: r.state in ['pending', 'approved']
            ))
    
    @api.constrains('max_registrations', 'current_registrations')
    def _check_registrations(self):
        for record in self:
            if record.max_registrations > 0 and record.current_registrations > record.max_registrations:
                raise ValidationError(_("Maximum registrations limit reached for this category."))
    
    def get_registration_fields(self):
        """Returns all registration fields including custom fields"""
        self.ensure_one()
        fields = []
        
        # Add standard fields
        standard_fields = [
            {
                'name': 'first_name',
                'field_key': 'first_name',
                'type': 'char',
                'required': True,
                'label': 'First Name',
                'placeholder': 'Enter your first name',
                'column_width': 'half'
            },
            {
                'name': 'last_name',
                'field_key': 'last_name',
                'type': 'char',
                'required': True,
                'label': 'Last Name',
                'placeholder': 'Enter your last name',
                'column_width': 'half'
            },
            {
                'name': 'email',
                'field_key': 'email',
                'type': 'email',
                'required': True,
                'label': 'Email Address',
                'placeholder': 'Enter your email address',
                'column_width': 'half'
            },
            {
                'name': 'phone',
                'field_key': 'phone',
                'type': 'phone',
                'required': False,
                'label': 'Phone Number',
                'placeholder': 'Enter your phone number',
                'column_width': 'half'
            },
            {
                'name': 'company',
                'field_key': 'company',
                'type': 'char',
                'required': False,
                'label': 'Company/Organization',
                'placeholder': 'Enter your company name',
                'column_width': 'half'
            },
            {
                'name': 'job_title',
                'field_key': 'job_title',
                'type': 'char',
                'required': False,
                'label': 'Job Title',
                'placeholder': 'Enter your job title',
                'column_width': 'half'
            }
        ]

        # Add ID and Photo fields if required
        if self.require_photo:
            standard_fields.append({
                'name': 'photo',
                'field_key': 'photo',
                'type': 'file',
                'required': True,
                'label': 'Photo',
                'help_text': 'Please upload a clear photo',
                'file_types': '.jpg,.jpeg,.png',
                'max_file_size': 5,
                'column_width': 'full'
            })

        if self.require_id:
            standard_fields.append({
                'name': 'id_document',
                'field_key': 'id_document',
                'type': 'file',
                'required': True,
                'label': 'ID Document',
                'help_text': 'Please upload a valid ID document',
                'file_types': '.jpg,.jpeg,.png,.pdf',
                'max_file_size': 5,
                'column_width': 'full'
            })

        fields.extend(standard_fields)
        
        # Add custom fields
        for field in self.custom_fields:
            field_data = {
                'name': field.name,
                'field_key': field.field_key,
                'type': field.field_type,
                'required': field.required,
                'label': field.name,
                'placeholder': field.placeholder,
                'help_text': field.help_text,
                'validation_regex': field.validation_regex,
                'validation_message': field.validation_message,
                'column_width': field.column_width,
                'sequence': field.sequence
            }
            
            if field.field_type in ['selection', 'radio']:
                field_data['options'] = field.get_selection_options()
            
            if field.field_type == 'file':
                field_data['file_types'] = field.file_types
                field_data['max_file_size'] = field.max_file_size
            
            if field.min_length:
                field_data['min_length'] = field.min_length
            
            if field.max_length:
                field_data['max_length'] = field.max_length
            
            if field.min_value:
                field_data['min_value'] = field.min_value
            
            if field.max_value:
                field_data['max_value'] = field.max_value
                
            fields.append(field_data)
            
        return sorted(fields, key=lambda x: x.get('sequence', 0))
    
    def get_form_validation_rules(self):
        """Returns JSON validation rules for the form"""
        self.ensure_one()
        rules = {}
        messages = {}
        
        # Add validation rules for standard fields
        rules.update({
            'first_name': {
                'required': True,
                'minlength': 2
            },
            'last_name': {
                'required': True,
                'minlength': 2
            },
            'email': {
                'required': True,
                'email': True
            }
        })
        
        # Add validation rules for custom fields
        for field in self.custom_fields:
            field_rules = {
                'required': field.required
            }
            
            if field.validation_regex:
                field_rules['pattern'] = field.validation_regex
                messages[f"{field.field_key}.pattern"] = field.validation_message
            
            if field.min_length:
                field_rules['minlength'] = field.min_length
            
            if field.max_length:
                field_rules['maxlength'] = field.max_length
            
            if field.min_value:
                field_rules['min'] = field.min_value
            
            if field.max_value:
                field_rules['max'] = field.max_value
            
            if field.field_type == 'file':
                field_rules['accept'] = field.file_types
                field_rules['maxsize'] = field.max_file_size * 1024 * 1024  # Convert to bytes
            
            rules[field.field_key] = field_rules
        
        return {
            'rules': rules,
            'messages': messages
        }
    
    def process_registration(self, form_data, files=None):
        """Process registration form submission"""
        self.ensure_one()
        
        # Check registration limit
        if self.max_registrations and self.current_registrations >= self.max_registrations:
            raise ValidationError(_("Registration limit reached for this category."))
        
        # Prepare registration data
        registration_vals = {
            'event_id': self.event_id.id,
            'category_id': self.id,
            'first_name': form_data.get('first_name'),
            'last_name': form_data.get('last_name'),
            'email': form_data.get('email'),
            'phone': form_data.get('phone'),
            'company': form_data.get('company'),
            'job_title': form_data.get('job_title'),
            'state': 'approved' if self.auto_approve else 'pending'
        }
        
        # Process custom fields
        custom_values = {}
        file_ids = []
        
        # Handle standard file fields (photo and ID)
        if self.require_photo and files.get('photo'):
            file = files['photo']
            file_data = {
                'name': file.filename,
                'field_key': 'photo',
                'file_data': base64.b64encode(file.read()),
                'file_type': file.content_type
            }
            file_ids.append((0, 0, file_data))

        if self.require_id and files.get('id_document'):
            file = files['id_document']
            file_data = {
                'name': file.filename,
                'field_key': 'id_document',
                'file_data': base64.b64encode(file.read()),
                'file_type': file.content_type
            }
            file_ids.append((0, 0, file_data))

        # Process custom fields
        for field in self.custom_fields:
            field_key = field.field_key
            
            if field.field_type == 'file' and files and field_key in files:
                file = files[field_key]
                file_data = {
                    'name': file.filename,
                    'field_key': field_key,
                    'file_data': base64.b64encode(file.read()),
                    'file_type': file.content_type
                }
                file_ids.append((0, 0, file_data))
            else:
                if field_key in form_data:
                    custom_values[field_key] = form_data[field_key]
        
        if custom_values:
            registration_vals['custom_field_values'] = json.dumps(custom_values)
        
        if file_ids:
            registration_vals['registration_files'] = file_ids
        
        # Create registration
        registration = self.env['event.mgmt.registration'].sudo().create(registration_vals)
        
        # Send confirmation email
        if self.confirmation_template_id:
            self.confirmation_template_id.send_mail(registration.id, force_send=True)
        
        return registration

    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.event_id.name}] {record.name}"
            result.append((record.id, name))
        return result