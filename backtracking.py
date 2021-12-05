import json
import yaml
import random
import calendar
from datetime import date, datetime, timedelta

from person import Person
from json_encoders import PersonEncoder


# Importing config from yaml
with open('config.yaml', 'r') as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as err:
        print(err)


# Empty planning setup
num_days = calendar.monthrange(config['year'], config['month'])[1]
planning = {date(config['year'], config['month'], day): [] for day in range(1, num_days+1)}


# Team init
employees = []

# Team setup + leaves + mandatory shifts
for employee in config['employees']:
    p = Person(employee['first_name'],
               employee['last_name'],
               employee['gender'])
    try:
        for leave in employee['leaves']:
            p.set_leave(start=leave['start_date'],
                        end=leave['end_date'])
        for d in employee['mandatory_shifts']:
            p.set_mandatory_shift(day=d)
    except KeyError:
        pass
    employees.append(p)


# Check for last month planning
def check_last_planning():
    previous_planning = (date(config['year'], config['month'], 1) - timedelta(days=1)).strftime('planning_%Y_%#m.json')
    try:
        with open(previous_planning, 'r') as json_file:
            shifts = json.load(json_file)
            for shift in list(shifts.items())[-4:]:
                day = datetime.strptime(shift[0], '%Y-%m-%d').date()
                for e in employees:
                    for last_name in shift[1]:
                        if last_name == e.last_name:
                            e.in_shift(day)
    except FileNotFoundError:
        print('Last month\'s planning not found')


# Init Blacklist (used for backtracking)
blacklist = []


def backtrack(plan, day, team, limit):
    global blacklist

    # Exit case (plan is complete)
    if list(plan.values())[-1]:
        return plan

    # randomly mix the team (for equity)
    random.shuffle(team)

    # Check mandatory shifts first
    for person in team:
        if person.check_mandatory_shift(day):
            plan[day].append(person)
            person.in_shift(day)

    # Main loop
    for person in team:
        # check if available (not in leave)
        if not person.is_available(day):
            continue
        # check if in blacklist (backtracking)
        if (person, day) in blacklist:
            continue
        # check if more than 2 people in shift
        elif len(plan[day]) >= limit:
            limit = 2
            break
        # check if genders match
        elif plan[day] and person.gender != plan[day][0].gender:
            continue
        # if all the above are met assign person to shift
        else:
            plan[day].append(person)
            person.in_shift(day)
    # If for loop exits without break (no person was found available)
    else:
        if not plan[day]:
            day -= timedelta(days=1)
            try:
                if len(plan[day]) == 2:
                    plan[day][0].remove_last_leave()
                    plan[day][1].remove_last_leave()
                    blacklist.append((plan[day][random.randint(0, 1)], day))
                elif len(plan[day]) == 1:
                    plan[day][0].remove_last_leave()
                    blacklist.append((plan[day][0], day))
                plan[day] = []
                for (person, d) in blacklist:
                    if d > day:
                        blacklist.remove((person, d))
            except KeyError:
                print('No possible solution!')
                exit()
            backtrack(plan, day, team, 1)  # previous day

    backtrack(plan, day + timedelta(days=1), team, limit)  # next day


# For shift continuity
check_last_planning()

# Call to main function
backtrack(plan=planning,
          day=list(planning.keys())[0],
          team=employees,
          limit=2)


planning = dict((day.isoformat(), value) for (day, value) in planning.items())

# Save planning to JSON
with open(f'planning_{config["year"]}_{config["month"]}.json', 'w') as outfile:
    json.dump(planning, outfile, indent=4, cls=PersonEncoder)
