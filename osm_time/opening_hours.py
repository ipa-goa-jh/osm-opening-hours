from collections import defaultdict

from osm_time import ParseException, clean_value, get_minutes_from_midnight

import re

# Days of the week + ph (public holiday)
DAYS_OF_THE_WEEK = ['su', 'mo', 'tu', 'we', 'th', 'fr', 'sa', 'ph']
MINUTES_FROM_SO = {'so': 0*1440, 'mo': 1*1440, 'tu': 2*1440, 'we': 3*1440, 'th': 4*1440, 'fr': 5*1440, 'sa': 6*1440}


class OpeningHours(object):

    def __init__(self, value):
        """
        @param value to parse
        """
        self.value = clean_value(value)
        self.is_always_open = False
        if self.value == "24/7":
            self.is_always_open = True
            return    # can't parse this value atm
        
        try:
            self.opening_hours = parse_string(self.value)
        except Exception as e:
            raise ParseException(value, e)

    def is_open(self, day, time):
        """
        Return True if open for given day and time, else False
        """
        if self.is_always_open: return True
        day = day.lower()

        if not day in self.opening_hours: return False

        for op_hours in self.opening_hours[day]:
            if op_hours[0] < get_minutes_from_midnight(time) < op_hours[1]:
                return True
        return False

    def minutes_to_closing(self, day, time):
        """
        Return 0 if closed for given day and time, else number of minutes to closing
        """
        if self.is_always_open: return -1   # TODO value for "not closing"?
        day = day.lower()

        if not day in self.opening_hours: return 0

        for op_hours in self.opening_hours[day]:
            if op_hours[0] < get_minutes_from_midnight(time) < op_hours[1]:
                return op_hours[1] - get_minutes_from_midnight(time)
        return 0

    def get_as_dictionnary(self):
        """
        Get parsed value as a dict of day containing ranges of opened times
        """
        return self.opening_hours


def parse_string(value):
    """
    Parse a string in the OSM format
    Returns a dict with day of the week as key and
    a list of range of opening hours
    """
    value = value.replace(',', ' ').replace(';', ' ')
    opening_hours = defaultdict(list)
    er = True
    #for definition in value.split('  '):
    if True:
        definition = value.strip()
        try:
            pos = 0
            while pos < len(definition):
                #print("definition", definition)
                # 1. try to find dayspan
                se = re.search(r'^(mo|tu|we|th|fr|sa|su)-(mo|tu|we|th|fr|sa|su)', definition)

                if not se:
                    # 2. try single day
                    se = re.search(r'^(mo|tu|we|th|fr|sa|su|ph)', definition)
                    if not se:
                        if er: print("Error: ", value)
                        er = False
                        pos += 1
                        definition = definition[pos:]
                        pos=0
                        continue
                    day_fr = DAYS_OF_THE_WEEK.index(se.group().strip())
                    day_t = day_fr
                else:
                    day_fr = DAYS_OF_THE_WEEK.index(se.groups()[0].strip())
                    day_t = DAYS_OF_THE_WEEK.index(se.groups()[1].strip())
                pos = se.end()

                while se:
                    definition = definition[pos:].strip()
                    pos = 0
                    #print("tmp", definition)
                    se = re.search(r'^\d\d:\d\d-\d\d:\d\d', definition)
                    if not se:
                        break

                    pos = se.end()

                    time = se.group()
                    #print("time: ", time)

                    for da in DAYS_OF_THE_WEEK[day_fr:day_t + 1]:
                        rg = process_ranges(time.strip())
                        if da in opening_hours:
                            opening_hours[da] += rg
                        else:
                            opening_hours[da] = rg
                definition = definition[pos:].strip()
                pos=0
                er = True
        except Exception as e:
            print("Error", e)
            print(value)
            print(definition)
            print(times)
            print(dayspans)
            print(days)
            raise
    return opening_hours


def process_ranges(ranges):
    """
    Processes a list of time ranges, returns a list of tuples
    """
    values = list()
    for ra in ranges.split(','):
        if ra != "off":
            values.append(process_time_range(ra))
    return values


def process_time_range(value):
    """
    Return a tuple with (from, to) time in minutes from midnight.
    """
    from_time, to_time = value.split('-')
    from_t = get_minutes_from_midnight(from_time)
    to_t = get_minutes_from_midnight(to_time)
    return (from_t, to_t)
