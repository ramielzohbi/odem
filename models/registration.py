# models/registration.py
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json
import base64

class EventMgmtRegistration(models.Model):
    _name = 'event.mgmt.registration'
    _description = 'Event Registration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Registration Number', readonly=True, copy=False, 
                      default=lambda self: _('New'))
    
    event_id = fields.Many2one('event.mgmt', string='Event', required=True, ondelete='cascade')
    category_id = fields.Many2one('event.mgmt.category', string='Category', required=True, ondelete='cascade',
                                 domain="[('event_id', '=', event_id)]")
    

    badge_printed = fields.Boolean(string="Badge Printed", default=False, tracking=True)
    badge_reprinted = fields.Boolean(string="Badge Reprinted", default=False, tracking=True)
    reprint_date = fields.Datetime(string="Reprint Date")
    reprint_user_id = fields.Many2one('res.users', string="Reprinted By")
    
    active = fields.Boolean(string="Active", default=True)

    photo = fields.Image(string="Photo")
    photo_validated = fields.Boolean(string="Photo Validated", default=False)

    id_document = fields.Image(string="ID Document")
    id_validated = fields.Boolean(string="ID Validated", default=False)

    ai_validation_result = fields.Text(string="AI Validation Result", readonly=True)
    badge_printed_by = fields.Many2one('res.users', string="Badge Printed By", readonly=True)
    badge_printed_date = fields.Datetime(string="Badge Printed Date", readonly=True)
    # badge_printed_ip = fields.Char(string="Badge Printed IP", readonly=True)
    # badge_printed_mac = fields.Char(string="Badge Printed MAC", readonly=True)
    # badge_printed_printer = fields.Char(string="Badge Printed Printer", readonly=True)
    # badge_printed_paper_size = fields.Char(string="Badge Printed Paper Size", readonly=True)
    # badge_printed_paper_orientation = fields.Char(string="Badge Printed Paper Orientation", readonly=True)

    # Base Fields
    first_name = fields.Char(string='First Name', required=True)
    last_name = fields.Char(string='Last Name', required=True)
    email = fields.Char(string='Email', required=True)
    phone = fields.Char(string='Phone')
    company = fields.Char(string='Company/Organization')
    job_title = fields.Char(string='Job Title')
    
    # Custom Fields Data
    custom_field_values = fields.Text(string='Custom Field Values')

    
    # Files
    registration_files = fields.One2many('event.mgmt.registration.file', 'registration_id', string='Uploaded Files')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status', default='draft', tracking=True)
    
    rejection_reason = fields.Text(string='Rejection Reason')
    
    # Computed Fields
    full_name = fields.Char(string='Full Name', compute='_compute_full_name', store=True)
    custom_fields = fields.Text(compute='_compute_custom_fields')

    @api.depends('first_name', 'last_name')
    def _compute_full_name(self):
        for record in self:
            record.full_name = f"{record.first_name or ''} {record.last_name or ''}".strip()

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('event.mgmt.registration') or _('New')
        return super(EventMgmtRegistration, self).create(vals)
    
    def print_badge(self):
        for record in self:
            record.badge_printed = True
            record.badge_printed_date = fields.Datetime.now()
            record.badge_printed_by = self.env.user.id
        return True

    def reprint_badge(self):
        """
        Allows reprinting of the badge by updating the reprint log.
        """
        for record in self:
            if not record.badge_printed:
                raise ValidationError(_("Cannot reprint a badge that has not been printed yet."))
            
            # Log the reprint details
            record.badge_reprinted = True  # Assuming you want to track if a badge was reprinted
            record.reprint_date = fields.Datetime.now()
            record.reprint_user_id = self.env.user.id
            
        return True


    def action_submit(self):
        for record in self:
            record.write({'state': 'pending'})
            if record.category_id.confirmation_template_id:
                record.category_id.confirmation_template_id.send_mail(record.id, force_send=True)
        return True

    def action_approve(self):
        for record in self:
            record.write({'state': 'approved'})
            if record.category_id.approval_template_id:
                record.category_id.approval_template_id.send_mail(record.id, force_send=True)
        return True

    def action_reject(self):
        for record in self:
            if not record.rejection_reason:
                raise ValidationError(_("Please provide a rejection reason."))
            record.write({'state': 'rejected'})
            if record.category_id.rejection_template_id:
                record.category_id.rejection_template_id.send_mail(record.id, force_send=True)
        return True

    def _compute_custom_fields(self):
        for record in self:
            if record.custom_field_values:
                try:
                    values = json.loads(record.custom_field_values)
                    formatted_values = []
                    for field in record.category_id.custom_fields:
                        if field.field_key in values:
                            value = values[field.field_key]
                            if field.field_type == 'selection':
                                options = dict(field.get_selection_options())
                                value = options.get(value, value)
                            formatted_values.append({
                                'label': field.name,
                                'value': value
                            })
                    record.custom_fields = json.dumps(formatted_values)
                except:
                    record.custom_fields = '{}'
            else:
                record.custom_fields = '{}'

class EventMgmtRegistrationFile(models.Model):
    _name = 'event.mgmt.registration.file'
    _description = 'Registration File'

    name = fields.Char(string='File Name', required=True)
    registration_id = fields.Many2one('event.mgmt.registration', string='Registration', 
                                    required=True, ondelete='cascade')
    field_key = fields.Char(string='Field Key', required=True)
    file_data = fields.Binary(string='File', required=True)
    file_type = fields.Char(string='File Type')
    file_size = fields.Float(string='File Size (MB)', compute='_compute_file_size', store=True)

    @api.depends('file_data')
    def _compute_file_size(self):
        for record in self:
            if record.file_data:
                # Convert to MB
                record.file_size = len(base64.b64decode(record.file_data)) / (1024 * 1024)
            else:
                record.file_size = 0
