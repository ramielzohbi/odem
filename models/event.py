from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class EventManagement(models.Model):
    _name = 'event.mgmt'
    _description = 'Event Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date desc, id desc'

    name = fields.Char(string='Event Name', required=True, translate=True)
    code = fields.Char(string='Event Code', required=True, copy=False, readonly=True,
                      default=lambda self: _('New'))
    
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    
    description = fields.Html(string='Description', translate=True)
    venue = fields.Char(string='Venue')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    # Website Fields
    website_published = fields.Boolean('Published on Website', copy=False)
    website_url = fields.Char('Website URL', compute='_compute_website_url')
    
    # Relationships
    category_ids = fields.One2many('event.mgmt.category', 'event_id', string='Categories')
    registration_ids = fields.One2many('event.mgmt.registration', 'event_id', string='Registrations')
    organizer_id = fields.Many2one('res.partner', string='Organizer', 
                                  domain="[('is_company', '=', True)]", tracking=True)
    
    company_id = fields.Many2one('res.company', string='Company', 
                                default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    
    total_registrations = fields.Integer(compute='_compute_registrations', store=True)
    active = fields.Boolean(default=True)

    # Compute methods
    @api.depends('name')
    def _compute_website_url(self):
        for event in self:
            event.website_url = f'/event/{event.id}'

    # Action methods remain the same
    def action_view_registrations(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("event_management.action_event_registration")
        action['context'] = {
            'default_event_id': self.id,
            'search_default_event_id': self.id,
        }
        if self.total_registrations == 1:
            registration = self.registration_ids[0]
            action['views'] = [(self.env.ref('event_management.view_event_registration_form').id, 'form')]
            action['res_id'] = registration.id
        return action

    def action_confirm(self):
        for record in self:
            record.write({'state': 'confirmed'})
        return True

    def action_start(self):
        for record in self:
            if record.state != 'confirmed':
                raise ValidationError(_("Event must be confirmed before starting."))
            record.write({'state': 'in_progress'})
        return True

    def action_close(self):
        for record in self:
            if record.state != 'in_progress':
                raise ValidationError(_("Event must be in progress before closing."))
            record.write({'state': 'done'})
        return True

    def action_cancel(self):
        for record in self:
            if record.state in ['done', 'cancelled']:
                raise ValidationError(_("Cannot cancel completed or already cancelled events."))
            record.write({'state': 'cancelled'})
        return True

    def action_reset_to_draft(self):
        for record in self:
            if record.state != 'cancelled':
                raise ValidationError(_("Only cancelled events can be reset to draft."))
            record.write({'state': 'draft'})
        return True

    @api.model
    def create(self, vals):
        if vals.get('code', _('New')) == _('New'):
            vals['code'] = self.env['ir.sequence'].next_by_code('event.mgmt') or _('New')
        return super(EventManagement, self).create(vals)
    
    @api.depends('registration_ids')
    def _compute_registrations(self):
        for event in self:
            event.total_registrations = len(event.registration_ids)
    
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise ValidationError(_("End date cannot be set before start date."))