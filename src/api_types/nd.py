from marshmallow import Schema, fields, EXCLUDE

from api_types.plaid import NDBSchema, TransactionSchema


class NDPayloadSchema(Schema):
    Sys_reqAmt = fields.Int(required=True)
    Sys_Time = fields.Str(required=True)
    Sys_payfreq = fields.Str(required=True)
    NDB = fields.Nested(NDBSchema, required=True)
    Historical_Transactions = fields.List(fields.Nested(TransactionSchema), required=True)

    class Meta:
        unknown = EXCLUDE


class NDOutput(Schema):
    ModelScore = fields.Int(required=True)
    NDBand = fields.Int(required=True)
