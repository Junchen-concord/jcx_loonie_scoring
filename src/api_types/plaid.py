from marshmallow import Schema, fields, EXCLUDE


class AddressSchema(Schema):
    streetAddressLine1 = fields.Str(required=True)
    streetAddressLine2 = fields.Str(allow_none=True)
    city = fields.Str(required=True)
    country = fields.Str(required=True)
    stateProvince = fields.Str(required=True)
    zipPostalCode = fields.Str(required=True)
    effectiveDate = fields.DateTime(allow_none=True)


class JobSchema(Schema):
    companyName = fields.Str(required=True)
    companyPhone = fields.Str(required=True)
    supervisorName = fields.Str(required=True)
    jobTitle = fields.Str(required=True)
    payFrequency = fields.Str(required=True)
    payNext = fields.Str(required=True)
    startDate = fields.Str(allow_none=True)


class ReferenceSchema(Schema):
    firstName = fields.Str(required=True)
    lastName = fields.Str(required=True)
    phone = fields.Str(required=True)
    email = fields.Email(allow_none=True)
    relationship = fields.Str(required=True)


class StatusHistorySchema(Schema):
    status = fields.Str(required=True)
    date = fields.DateTime(required=True)
    comments = fields.Str(allow_none=True)
    reason = fields.Str(allow_none=True)


class ResultSchema(Schema):
    id = fields.Str(required=True)
    lender = fields.Str(required=True)
    requestId = fields.Str(required=True, data_key="requestId")
    referenceId = fields.Str(allow_none=True)
    customerReferenceId = fields.Str(allow_none=True)
    firstName = fields.Str(required=True)
    lastName = fields.Str(required=True)
    dateOfBirth = fields.Str(required=True)
    address = fields.Nested(AddressSchema, required=True)
    phone1 = fields.Str(required=True)
    phone2 = fields.Str(allow_none=True)
    fax = fields.Str(allow_none=True)
    email = fields.Email(required=True)
    job = fields.Nested(JobSchema, required=True)
    references = fields.List(fields.Nested(ReferenceSchema), required=True)
    amount = fields.Float(required=True)
    balance = fields.Float(allow_none=True)
    requestDate = fields.DateTime(required=True)
    ipAddress = fields.Str(required=True)
    language = fields.Str(required=True)
    language_id = fields.Int(required=True)
    status = fields.Str(required=True)
    comments = fields.Str(allow_none=True)
    statusHistory = fields.List(fields.Nested(StatusHistorySchema), required=True)
    canRenew = fields.Bool(required=True)
    renewalUrl = fields.Str(allow_none=True)
    canSolicit = fields.Bool(required=True)
    snoozeUntil = fields.DateTime(allow_none=True)
    revisions = fields.Int(required=True)
    createdAt = fields.DateTime(required=True)
    lastUpdatedAt = fields.DateTime(required=True)


class ScoreSchema(Schema):
    scoreEnabled = fields.Bool(required=True)
    score = fields.Float(allow_none=True)
    reasons = fields.List(fields.Str(), required=True)


class QuerySchema(Schema):
    referenceId = fields.Str(allow_none=True)
    firstName = fields.Str(required=True)
    lastName = fields.Str(required=True)
    dateOfBirth = fields.Str(required=True)
    phone = fields.Str(required=True)
    email = fields.Email(required=True)
    ipAddress = fields.Str(allow_none=True)
    accuracy = fields.Int(required=True)
    score = fields.Bool(required=True)
    track = fields.Bool(required=True)


class NDBSchema(Schema):
    accountnumber = fields.Int(required=True)
    search_query_id = fields.Str(required=True)
    results = fields.List(fields.Nested(ResultSchema), required=True)
    count = fields.Int(required=True)
    pages = fields.Int(required=True)
    total_count = fields.Int(required=True)
    score = fields.Nested(ScoreSchema, required=True)
    score_requested = fields.Bool(required=True)
    billed = fields.Bool(required=True)
    cached = fields.Bool(required=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(allow_none=True)
    query = fields.Nested(QuerySchema, required=True)


class TransactionSchema(Schema):
    name = fields.Str(required=True)
    transaction_id = fields.Str(required=True)
    account_id = fields.Str(required=True)
    category = fields.List(fields.Str(), required=True)
    category_id = fields.Str(required=True)
    transaction_type = fields.Int(required=True)
    payment_channel = fields.Int(required=True)
    TransactionCode = fields.Int(required=True)
    amount = fields.Float(required=True)
    CurrencyCode = fields.Str(required=True)
    date = fields.DateTime(required=True)
    authorized_date = fields.DateTime(allow_none=True)


class PlaidPayloadSchema(Schema):
    Model1Score = fields.Int(required=True)
    NDBand = fields.Int(required=True)
    Sys_reqAmt = fields.Int(required=True)
    Sys_Time = fields.Str(required=True)
    Sys_payfreq = fields.Str(required=True)
    NDB = fields.Nested(NDBSchema, required=True)
    Historical_Transactions = fields.List(fields.Nested(TransactionSchema), required=True)

    class Meta:
        unknown = EXCLUDE


class PlaidOutput(Schema):
    ModelScore = fields.Int(required=True)
    IBVBand = fields.Int(required=True)
