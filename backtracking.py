import json
import yaml
import random
import pandas
import calendar
from datetime import timedelta, date

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
workers = []

# Team setup + leaves + mandatory shifts
for worker in config['workers']:
    p = Person(worker['first_name'],
               worker['last_name'],
               worker['gender'])
    try:
        for leave in worker['leaves']:
            p.set_leave(start=leave['start_date'],
                        end=leave['end_date'])
        for date in worker['mandatory_shifts']:
            p.set_mandatory_shift(day=date)
    except KeyError:
        pass
    workers.append(p)


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


# Call to main function
backtrack(plan=planning,
          day=list(planning.keys())[0],
          team=workers,
          limit=2)


planning = dict((day.isoformat(), value) for (day, value) in planning.items())


# Save planning to JSON
with open(f'planning_{config["year"]}_{config["month"]}.json', 'w') as outfile:
    json.dump(planning, outfile, indent=4, cls=PersonEncoder)


# Save planning to Excel (rudimentary)
df = pandas.DataFrame.from_dict(data=planning, orient='index')
df = df.transpose()
df.to_excel(f'planning_{config["year"]}_{config["month"]}.xlsx')
