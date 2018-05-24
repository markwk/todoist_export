# Todoist Export for Python 3

from todoist.api import TodoistAPI

import pandas as pd

from datetime import datetime

import json

# Authentification
with open("credentials.json", "r") as file:
    credentials = json.load(file)
    todoist_cr = credentials['todoist']
    TOKEN = todoist_cr['TOKEN']

api = TodoistAPI(TOKEN)

# Intitial Sync
api.sync()

# User Info
user = api.state['user']
user_name = user['full_name']

# Stats: Tasks Completed by User
user_completed_count = user['completed_count']

#  User Projects
user_projects  = api.state['projects']
with open('data/todoist-projects.csv', 'w') as file:
    file.write("Id" + "," + "Project" + "\n")
    for i in range(0, len(user_projects)):
        file.write('\"' + str(user_projects[i]['id']) + '\"' + "," + '\"' + str(user_projects[i]['name']) + '\"' + "\n")
print("Creating Export of Current Todoist Projects")
projects = pd.read_csv("data/todoist-projects.csv")

# User Stats
stats = api.completed.get_stats()

# total completed tasks from stats
user_completed_stats = stats['completed_count']
user_completed_stats

# Export Completed Todoist Items
def get_completed_todoist_items():
    # create df from initial 50 completed tasks
    print("Collecting Initial 50 Completed Todoist Tasks...")
    temp_tasks_dict = (api.completed.get_all(limit=50))
    past_tasks = pd.DataFrame.from_dict(temp_tasks_dict['items'])
    # get the remaining items
    pager = list(range(50,user_completed_count,50))
    for count, item in enumerate(pager):
        tmp_tasks = (api.completed.get_all(limit=50, offset=item))
        tmp_tasks_df = pd.DataFrame.from_dict(tmp_tasks['items'])
        past_tasks = pd.concat([past_tasks, tmp_tasks_df])
        print("Collecting Additional Todoist Tasks " + str(item) + " of " + str(user_completed_count))
    # save to CSV
    print("...Generating CSV Export")
    past_tasks.to_csv("data/todost-raw-tasks-completed.csv", index=False)

get_completed_todoist_items()
past_tasks = pd.read_csv("data/todost-raw-tasks-completed.csv")

# past_tasks.head()

# generated count 
collected_total = len(past_tasks)

# Does our collected total tasks match stat of completed count on user
print("Does our export of past completed tasks match user stats of completed task count?")
print(collected_total == user_completed_count)

past_tasks['project_id'] = past_tasks.project_id.astype('category')

# Extract all project ids used on tasks
project_ids = past_tasks.project_id.unique()

# get project info from Todoist API
def get_todoist_project_name(project_id):
    item = api.projects.get_by_id(project_id)
    if item: 
        try:
            return item['name']
        except:
            return item['project']['name']

# Get Info on All User Projects
project_names = []
for i in project_ids:
    project_names.append(get_todoist_project_name(i))

# Probably a more effecient way to do this
project_lookup = lambda x: get_todoist_project_name(x)
print("Assigning Project Name on Tasks...")
past_tasks['project_name'] = past_tasks['project_id'].apply(project_lookup)

# Add Day of Week Completed
past_tasks['completed_date'] = pd.to_datetime(past_tasks['completed_date'])
past_tasks['dow'] = past_tasks['completed_date'].dt.weekday
past_tasks['day_of_week'] = past_tasks['completed_date'].dt.weekday_name

# save to CSV
past_tasks.to_csv("data/todost-tasks-completed.csv", index=False)

# Export of Current Tasks
# Hackish Solution, Needs Improvement
available_task_items = api.state['items']
with open('data/current-tasks-raw.csv', 'w') as file:
    print("Generating and Creating A Raw Export of Current Todoist Tasks")
    file.write("id,content,checked,date_string,project_id,date_added,due_date_utc,date_completed \n")
    for i in list(range(0, len(available_task_items))): 
        if (available_task_items[i]['checked'] == 0):
            id = available_task_items[i]['id']
            content = available_task_items[i]['content']
            checked = available_task_items[i]['checked']
            date_string = available_task_items[i]['date_string']
            date_added = available_task_items[i]['date_added']
            project_id = available_task_items[i]['project_id']
            due_date_utc = available_task_items[i]['due_date_utc']
            date_completed = available_task_items[i]['date_completed']
            # print("id + "," + str(due_date_utc))
            file.write(str(id) 
                       + "," + '\"' + content + '\"' + "," 
                       + str(checked) + "," 
                       # + str(date_string) + "," 
                       + str(date_added)  + "," 
                       + str(project_id)  + "," 
                       + str(due_date_utc)  + "," 
                       + str(date_completed)                   
                       + "\n")

# df of current tasks
currents_task = pd.read_csv('data/current-tasks-raw.csv')

# Add project name to df
currents_task['project_name'] = currents_task['project_id'].apply(project_lookup)

# Date Added Cleanup
currents_task['date_added'] = currents_task['date_added'].replace(to_replace="None", value='')

# Add Day of Week Added
currents_task['date_added'] = pd.to_datetime(currents_task['date_added'])
currents_task['dow_added'] = currents_task['date_added'].dt.weekday
currents_task['day_of_week_added'] = currents_task['date_added'].dt.weekday_name

print("Generating Processed Export of Current Todoist Tasks")
currents_task.to_csv('data/current-tasks.csv', index=False)
