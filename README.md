[![Generic badge](https://img.shields.io/badge/python_version-3.9.0-blue.svg)](https://shields.io/)
# ShiftMaker

### About
Python algorithm used for scheduling 24hr work shifts. It uses backtracking to figure out
what employee to assign to a shift day.

### How to use
The configuration is done through _config.yaml_ file which has fields for selecting the month and year,
 employees and their leaves,  mandatory shifts or free days.

Example config:

```yaml
year: <int:YYYY>
month: <int:MM>
employees: 
  - first_name: <str>
    last_name: <str>
    gender: <str:(M/F)>
    leaves: 
      - end_date: <str:YYYY-MM-DD>
        start_date: <str:YYYY-MM-DD>
    mandatory_shifts: 
      - <str:YYYY-MM-DD>
    free_days:
      - <str:YYYY-MM-DD>
    <or>
    free_days: <int>
```

### Outputs
The algorithm generates the planning in __json__ format in the same folder
with the name ___planning_YEAR_MONTH.json___.

### TODO

 - [ ] make free_days for in_shift reduce from 3 to 2 if backtracking finds no solutions (and keep track of free days)
 - [ ] write tests
 - [x] keep track of free days (assign them randomly or at will)
 - [x] keep track of leaves
 - [x] assign employees to specific days
 - [x] gender-specific shifts (for whatever reason, duh)
 - [x] keep track of last month's planning (for continuity)
 - [x] wrote code for non-existent planning (backtracking found no solution)