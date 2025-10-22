"""
Constants/definitions for EDI Parser
Extracted from Bots botsconfig.py
"""

# ***for statust in ta:
OPEN     = 0  # Transaction open (error state)
ERROR    = 1  # Error in transaction
OK       = 2  # Successful
DONE     = 3  # Successful and picked up
RESEND   = 4  # File has been resent
NO_RETRY = 5  # No retry

# ***for status in ta:
PROCESS = 1
DISCARD = 3

EXTERNIN   = 200  # File is imported
FILEIN     = 220  # Received edi file
PARSED     = 310  # Edi file is lexed and parsed
SPLITUP    = 320  # Messages in the edi file have been split up
TRANSLATED = 330  # Result of translation
MERGED     = 400  # Envelope and/or merged
FILEOUT    = 500  # File is enveloped; ready for out
EXTERNOUT  = 520  # File is exported

# ***grammar.structure: keys in grammar records (dicts)
ID = 0
MIN = 1
MAX = 2
COUNT = 3
LEVEL = 4
MPATH = 5
FIELDS = 6
QUERIES = 7
SUBTRANSLATION = 8
BOTSIDNR = 9
FIXED_RECORD_LENGTH = 10  # Length of fixed record
CONTAINER = 11  # True if this is a container loop (not matchable segment)

# ***grammar.recorddefs: dict keys for fields of record
# eg: record[FIELDS][ID] == 'C124.0034'
# ID = 0 (is already defined)
MANDATORY = 1
LENGTH = 2
SUBFIELDS = 2  # For composites
FORMAT = 3  # Format in grammar file
ISFIELD = 4
DECIMALS = 5
MINLENGTH = 6
BFORMAT = 7  # Internal bots format; formats in grammar are converted to bformat
MAXREPEAT = 8

# ***lex_record in self.lex_records: is a dict
VALUE = 0
SFIELD = 1  # 1: is subfield, 0: field or first element composite
LIN = 2
POS = 3
FIXEDLINE = 4  # For fixed records; tmp storage of fixed record
FORMATFROMGRAMMAR = 5  # To store FORMAT field has in grammar
