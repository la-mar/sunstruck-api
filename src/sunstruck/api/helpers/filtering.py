import itertools
import re
from urllib import parse as urlparse

import pandas as pd

urlparse.parse_qs("filter=field:ge:7:lt:10")

regex = r"""
        # (?:\?filter=)?
        (?P<conjunctive>[:|]?)
        (?P<field_name>[:|]?\w+[^:|'\"])?
        (?P<sep>[:|])
        (?P<inverter>~)?
        (?P<operator>eq|gte|gt|lte|lt|in|between|regex|like)
        (?=:(?P<value>
        (?P<quoted>['\"][^'\"\\]*(?:\\.[^'\\]*)*['\"])
        |
        (?:(?P<unquoted>[^:|\s]*[^'\":|\s]))
        ))
        """

pattern = re.compile(regex, re.VERBOSE)

compound = [
    '?filter=field:gte:7|other_field:~in:a,b,c:another_field:between:"2020-01-01T17:22:20.937752,2020-01-31T17:22:20.937752":yet_another_field:eq:2020'  # noqa
]

equality = [
    "?filter=field:eq:7",
    '?filter=field:eq:"help"',
    "?filter=field:~eq:7",
    '?filter=field:~eq:"help"',
]

inequality = [
    "?filter=field:gt:7",
    # "?filter=field:lt:2020-01-01T17\\:22\\:20.937752",
    "?filter=field:gte:7",
    "?filter=field:gt:7|lt:14",
    "?filter=field:gte:7:lte:14",
    "?filter=field:gt:7:other_field:lt:10",
    "?filter=field:gte:7|other_field:lte:10",
    "?filter=field:gt:7|lt:14:other_field:gt:50:another_field:eq:100",
]

membership = [
    "?filter=field:in:a,b,c",
    "?filter=field:in:a,b,c:in:1,2,3",
    "?filter=field:in:a,b,c|in:1,2,3",
    "?filter=field:in:a,b,c:other_field:in:a,b,c",
    "?filter=field:in:a,b,c|other_field:in:1,2,3",
    "?filter=field:~in:a,b,c",
    "?filter=field:~in:a,b,c:~in:1,2,3",
    "?filter=field:~in:a,b,c|~in:1,2,3",
    "?filter=field:~in:a,b,c:other_field:~in:a,b,c",
    "?filter=field:~in:a,b,c|other_field:~in:1,2,3",
    "?filter=field:between:2020-01-01,2020-01-31",
    '?filter=field:between:"2020-01-01T17:22:20.937752,2020-01-31T17:22:20.937752"',
    "?filter=field:between:1,10",
    "?filter=field:between:1,10:other_field:between:100,200",
]

similarity = [
    '?filter=field:regex:"?.*val-(.*)"',
    '?filter=field:regex:"?.*val-(.*)":regex:".*"',
    '?filter=field:regex:"?.*val-(.*)"|regex:".*"',
    '?filter=field:regex:"?.*val-(.*)":other_field:regex:".*"',
    '?filter=field:regex:"?.*val-(.*)"|other_field:regex:".*"',
    '?filter=field:like:"*bueno"',
    '?filter=field:like:"mui:bueno"',
    '?filter=field:like:"*bueno"|like:"*bueno"',
    '?filter=field:like:"*bueno":other_field:like:"*bueno"',
    '?filter=field:like:"*bueno"|other_field:like:"*bueno"',
    '?filter=field:like:"*mui:bueno":other_field:like:"*bueno"',
    '?filter=field:like:"*mui|bueno"|other_field:like:"*bueno"',
]

strings = compound + equality + inequality + membership + similarity
records = []


matches = list(itertools.chain(*[pattern.findall(s) for s in strings]))


records = [dict(zip(pattern.groupindex, m)) for m in matches]

# record = [{k: v for k, v in m.items() if v} for m in mapped]
# records += record


records[0]


pd.options.display.max_rows = 100
pd.options.display.max_columns = 0
pd.options.display.expand_frame_repr = True
pd.options.display.large_repr = "truncate"
pd.options.display.float_format = lambda x: "%.2f" % x
pd.options.display.precision = 2
pd.options.display.max_colwidth = 100

pd.DataFrame(records)


# if there is no command, field_or_value should always be a field name
