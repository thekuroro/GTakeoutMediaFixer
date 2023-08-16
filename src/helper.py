# Helper function for converting decimal degrees to DMS (source: http://rextester.com/BRMA94677)
from math import floor


def dd2dms(decimal_degree: float, direction: str):
    if type(decimal_degree) != 'float':
        try:
            decimal_degree = float(decimal_degree)
        except:
            print('\nERROR: Could not convert %s to float.' % (type(decimal_degree)))
            return 0
    if decimal_degree < 0:
        decimal_degree = -decimal_degree
        if direction == 'longitude':
            appendix = 'W'
        else:
            appendix = 'S'
    else:
        if direction == 'longitude':
            appendix = 'E'
        else:
            appendix = 'N'
    minutes = decimal_degree % 1.0 * 60
    seconds = minutes % 1.0 * 60

    return (int(floor(decimal_degree)), int(floor(minutes)), seconds), appendix