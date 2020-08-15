"""

DataFrame output of parsing multiple queries:

   conjunctive         field_name sep inverter operator                                                    value                                                   quoted               unquoted
0                           field   :               gte                                                        7                                                                               7
1            |        other_field   :        ~       in                                                    a,b,c                                                                           a,b,c
2            :      another_field   :           between  "2020-01-01T17:22:20.937752,2020-01-31T17:22:20.937752"  "2020-01-01T17:22:20.937752,2020-01-31T17:22:20.937752"
3            :  yet_another_field   :                eq                                                     2020                                                                            2020
4                           field   :                eq                                                        7                                                                               7
5                           field   :                eq                                                   "help"                                                   "help"
6                           field   :        ~       eq                                                        7                                                                               7
7                           field   :        ~       eq                                                   "help"                                                   "help"
8                           field   :                gt                                                        7                                                                               7
9                           field   :               gte                                                        7                                                                               7
10                          field   :                gt                                                        7                                                                               7
11                                  |                lt                                                       14                                                                              14
12                          field   :               gte                                                        7                                                                               7
13                                  :               lte                                                       14                                                                              14
14                          field   :                gt                                                        7                                                                               7
15           :        other_field   :                lt                                                       10                                                                              10
16                          field   :               gte                                                        7                                                                               7
17           |        other_field   :               lte                                                       10                                                                              10
18                          field   :                gt                                                        7                                                                               7
19                                  |                lt                                                       14                                                                              14
20           :        other_field   :                gt                                                       50                                                                              50
21           :      another_field   :                eq                                                      100                                                                             100
22                          field   :                in                                                    a,b,c                                                                           a,b,c
23                          field   :                in                                                    a,b,c                                                                           a,b,c
24                                  :                in                                                    1,2,3                                                                           1,2,3
25                          field   :                in                                                    a,b,c                                                                           a,b,c
26                                  |                in                                                    1,2,3                                                                           1,2,3
27                          field   :                in                                                    a,b,c                                                                           a,b,c
28           :        other_field   :                in                                                    a,b,c                                                                           a,b,c
29                          field   :                in                                                    a,b,c                                                                           a,b,c
30           |        other_field   :                in                                                    1,2,3                                                                           1,2,3
31                          field   :        ~       in                                                    a,b,c                                                                           a,b,c
32                          field   :        ~       in                                                    a,b,c                                                                           a,b,c
33                                  :        ~       in                                                    1,2,3                                                                           1,2,3
34                          field   :        ~       in                                                    a,b,c                                                                           a,b,c
35                                  |        ~       in                                                    1,2,3                                                                           1,2,3
36                          field   :        ~       in                                                    a,b,c                                                                           a,b,c
37           :        other_field   :        ~       in                                                    a,b,c                                                                           a,b,c
38                          field   :        ~       in                                                    a,b,c                                                                           a,b,c
39           |        other_field   :        ~       in                                                    1,2,3                                                                           1,2,3
40                          field   :           between                                    2020-01-01,2020-01-31                                                           2020-01-01,2020-01-31
41                          field   :           between  "2020-01-01T17:22:20.937752,2020-01-31T17:22:20.937752"  "2020-01-01T17:22:20.937752,2020-01-31T17:22:20.937752"
42                          field   :           between                                                     1,10                                                                            1,10
43                          field   :           between                                                     1,10                                                                            1,10
44           :        other_field   :           between                                                  100,200                                                                         100,200
45                          field   :             regex                                            "?.*val-(.*)"                                            "?.*val-(.*)"
46                          field   :             regex                                            "?.*val-(.*)"                                            "?.*val-(.*)"
47                                  :             regex                                                     ".*"                                                     ".*"
48                          field   :             regex                                            "?.*val-(.*)"                                            "?.*val-(.*)"
49                                  |             regex                                                     ".*"                                                     ".*"
50                          field   :             regex                                            "?.*val-(.*)"                                            "?.*val-(.*)"
51           :        other_field   :             regex                                                     ".*"                                                     ".*"
52                          field   :             regex                                            "?.*val-(.*)"                                            "?.*val-(.*)"
53           |        other_field   :             regex                                                     ".*"                                                     ".*"
54                          field   :              like                                                 "*bueno"                                                 "*bueno"
55                          field   :              like                                              "mui:bueno"                                              "mui:bueno"
56                          field   :              like                                                 "*bueno"                                                 "*bueno"
57                                  |              like                                                 "*bueno"                                                 "*bueno"
58                          field   :              like                                                 "*bueno"                                                 "*bueno"
59           :        other_field   :              like                                                 "*bueno"                                                 "*bueno"
60                          field   :              like                                                 "*bueno"                                                 "*bueno"
61           |        other_field   :              like                                                 "*bueno"                                                 "*bueno"
62                          field   :              like                                             "*mui:bueno"                                             "*mui:bueno"
63           :        other_field   :              like                                                 "*bueno"                                                 "*bueno"
64                          field   :              like                                             "*mui|bueno"                                             "*mui|bueno"
65           |        other_field   :              like                                                 "*bueno"                                                 "*bueno"


"""  # noqa

# import itertools
# import pandas as pd
# from api.helpers import pattern

# compound = [
#     '?filter=field:gte:7|other_field:~in:a,b,c:another_field:between:"2020-01-01T17:22:20.937752,2020-01-31T17:22:20.937752":yet_another_field:eq:2020'  # noqa
# ]

# equality = [
#     "?filter=field:eq:7",
#     '?filter=field:eq:"help"',
#     "?filter=field:~eq:7",
#     '?filter=field:~eq:"help"',
# ]

# inequality = [
#     "?filter=field:gt:7",
#     # "?filter=field:lt:2020-01-01T17\\:22\\:20.937752",
#     "?filter=field:gte:7",
#     "?filter=field:gt:7|lt:14",
#     "?filter=field:gte:7:lte:14",
#     "?filter=field:gt:7:other_field:lt:10",
#     "?filter=field:gte:7|other_field:lte:10",
#     "?filter=field:gt:7|lt:14:other_field:gt:50:another_field:eq:100",
# ]

# membership = [
#     "?filter=field:in:a,b,c",
#     "?filter=field:in:a,b,c:in:1,2,3",
#     "?filter=field:in:a,b,c|in:1,2,3",
#     "?filter=field:in:a,b,c:other_field:in:a,b,c",
#     "?filter=field:in:a,b,c|other_field:in:1,2,3",
#     "?filter=field:~in:a,b,c",
#     "?filter=field:~in:a,b,c:~in:1,2,3",
#     "?filter=field:~in:a,b,c|~in:1,2,3",
#     "?filter=field:~in:a,b,c:other_field:~in:a,b,c",
#     "?filter=field:~in:a,b,c|other_field:~in:1,2,3",
#     "?filter=field:between:2020-01-01,2020-01-31",
#     '?filter=field:between:"2020-01-01T17:22:20.937752,2020-01-31T17:22:20.937752"',
#     "?filter=field:between:1,10",
#     "?filter=field:between:1,10:other_field:between:100,200",
# ]

# similarity = [
#     '?filter=field:regex:"?.*val-(.*)"',
#     '?filter=field:regex:"?.*val-(.*)":regex:".*"',
#     '?filter=field:regex:"?.*val-(.*)"|regex:".*"',
#     '?filter=field:regex:"?.*val-(.*)":other_field:regex:".*"',
#     '?filter=field:regex:"?.*val-(.*)"|other_field:regex:".*"',
#     '?filter=field:like:"*bueno"',
#     '?filter=field:like:"mui:bueno"',
#     '?filter=field:like:"*bueno"|like:"*bueno"',
#     '?filter=field:like:"*bueno":other_field:like:"*bueno"',
#     '?filter=field:like:"*bueno"|other_field:like:"*bueno"',
#     '?filter=field:like:"*mui:bueno":other_field:like:"*bueno"',
#     '?filter=field:like:"*mui|bueno"|other_field:like:"*bueno"',
# ]

# strings = compound + equality + inequality + membership + similarity
# records = []


# matches = list(itertools.chain(*[pattern.findall(s) for s in strings]))


# records = [dict(zip(pattern.groupindex, m)) for m in matches]


# pd.options.display.max_rows = 100
# pd.options.display.max_columns = 0
# pd.options.display.expand_frame_repr = True
# pd.options.display.large_repr = "truncate"
# pd.options.display.float_format = lambda x: "%.2f" % x
# pd.options.display.precision = 2
# pd.options.display.max_colwidth = 100

# pd.DataFrame(records)
