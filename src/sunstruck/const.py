from util.enums import Enum


class FilterOperator(str, Enum):

    IS = "is"
    EQ = "eq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    LIKE = "like"
    IN = "in"
    BETWEEN = "between"
