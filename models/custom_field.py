# models/custom_field.py
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json

class EventMgmtCategoryField(models.Model):
    _name = 'event.mgmt.category.field'
    _description = 'Custom Registration Field'
    _order = 'sequence, id'

    name = fields.Char(string='Field Label', required=True, translate=True)
    field_key = fields.Char(string='Field Key', required=True, help="Technical name for the field")
    category_id = fields.Many2one('event.mgmt.category', string='Category', required=True, ondelete='cascade')
    field_type = fields.Selection([
        ('char', 'Single Line Text'),
        ('text', 'Multi Line Text'),
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('selection', 'Selection'),
        ('radio', 'Radio Buttons'),
        ('checkbox', 'Checkbox'),
        ('date', 'Date'),
        ('datetime', 'Date & Time'),
        ('file', 'File Upload')
    ], string='Field Type', required=True, default='char')
    
    sequence = fields.Integer(string='Sequence', default=10)
    required = fields.Boolean(string='Required', default=False)
    placeholder = fields.Char(string='Placeholder', translate=True)
    help_text = fields.Char(string='Help Text', translate=True)
    validation_regex = fields.Char(string='Validation Pattern')
    validation_message = fields.Char(string='Validation Message', translate=True)
    
    # For selection/radio fields
    selection_options = fields.Text(
        string='Options', 
        help='Enter one option per line. Format: value|label'
    )
    
    # Additional field attributes
    min_length = fields.Integer(string='Minimum Length')
    max_length = fields.Integer(string='Maximum Length')
    min_value = fields.Float(string='Minimum Value')
    max_value = fields.Float(string='Maximum Value')
    file_types = fields.Char(string='Allowed File Types', help="Comma-separated list of file extensions (e.g., .pdf,.doc)")
    max_file_size = fields.Integer(string='Maximum File Size (MB)', default=5)
    
    column_width = fields.Selection([
        ('full', 'Full Width'),
        ('half', 'Half Width')
    ], string='Column Width', default='full')

    _sql_constraints = [
        ('unique_field_key_per_category', 
         'unique(category_id, field_key)', 
         'Field Key must be unique per category!')
    ]

    @api.model
    def create(self, vals):
        if 'field_key' in vals:
            vals['field_key'] = self._sanitize_field_key(vals['field_key'])
        return super(EventMgmtCategoryField, self).create(vals)

    def write(self, vals):
        if 'field_key' in vals:
            vals['field_key'] = self._sanitize_field_key(vals['field_key'])
        return super(EventMgmtCategoryField, self).write(vals)

    def _sanitize_field_key(self, field_key):
        """Sanitize field key to be a valid technical name"""
        if not field_key:
            return field_key
        # Replace spaces and special chars with underscore
        sanitized = ''.join(c if c.isalnum() else '_' for c in field_key.lower())
        # Remove consecutive underscores
        while '__' in sanitized:
            sanitized = sanitized.replace('__', '_')
        # Remove leading/trailing underscores
        return sanitized.strip('_')

    @api.constrains('field_key')
    def _check_field_key(self):
        """Ensure field_key doesn't conflict with base fields"""
        base_fields = ['id', 'create_date', 'write_date', 'create_uid', 'write_uid',
                      'name', 'event_id', 'category_id', 'state']
        for record in self:
            if record.field_key in base_fields:
                raise ValidationError(_("Field Key '%s' is reserved. Please choose another name.") % record.field_key)

    def get_selection_options(self):
        """Return formatted selection options"""
        self.ensure_one()
        if not self.selection_options:
            return []
        options = []
        for line in self.selection_options.split('\n'):
            if '|' in line:
                value, label = line.strip().split('|', 1)
                options.append((value.strip(), label.strip()))
            else:
                line = line.strip()
                options.append((line, line))
        return options

    def get_field_validation_rules(self):
        """Return field validation rules as JSON"""
        self.ensure_one()
        rules = {
            'required': self.required,
            'type': self.field_type,
        }
        
        if self.validation_regex:
            rules['pattern'] = self.validation_regex
            rules['pattern_message'] = self.validation_message or 'Invalid format'
            
        if self.min_length:
            rules['minlength'] = self.min_length
            
        if self.max_length:
            rules['maxlength'] = self.max_length
            
        if self.min_value:
            rules['min'] = self.min_value
            
        if self.max_value:
            rules['max'] = self.max_value
            
        if self.field_type == 'file':
            rules['file_types'] = self.file_types
            rules['max_file_size'] = self.max_file_size
            
        return json.dumps(rules)
