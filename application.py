from flask import Flask, render_template, flash, request
from wtforms import Form, TextField, TextAreaField, validators, StringField, SubmitField
import pickle
import urllib.request
 
# App config.
DEBUG = True
app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = '7d441f27d441f27567d441f2b6176a'
 
class ReusableForm(Form):
    name = TextField('Name:', validators=[validators.required()])
 
# set up the champion pool stuff
with urllib.request.urlopen('https://cdn.rawgit.com/puhseechee/champion_pool/67be5e03/objs.pkl') as f:
    rnames, codenames, champions, winrates, names, pickrates = pickle.load(f)

#%% code for computing safety profile
# return for each champion their worst matchup winrate in the specified role
# useful for identifying safe champions one can reliably pick early
def worst_winrates_single(champion_pool, role):
    # populate with worst winrate for each champion
    worst_winrates = []
    
    for each_champion in champion_pool:
        # get codename and index associated with champion/role
        # seek weakest matchup for each champion and store the winrate
        champ_index = champion_index(each_champion, role)
        weakest = 100.0
        for i in range(len(winrates[champ_index])):
            opponent = champions[champ_index][i]
            winrate = float(winrates[champ_index][i])
            if winrate < weakest:
                weakest = winrate

        # save result of searchc
        worst_winrates.append(weakest)
    
    champion_pool = sort_names_by_values(champion_pool, worst_winrates)
    return champion_pool, sorted(worst_winrates)

# similar, but computes for broader champion pool than indiviually
# useful for checking whether pool's bases have been covered
def worst_winrate_pool(champion_pool, role):
    # return the lowest winrate of the champion pool after collating
    return min(pool_winrates(champion_pool, role).values())

# takes two codenamed champions and returns difference between their winrates
def worst_winrate_compare(champx, champy):
    worstx = worst_winrates_single([names[champx]], champx[champx.find('\t')+1:])[0]
    worsty = worst_winrates_single([names[champy]], champy[champy.find('\t')+1:])[0]
    return worstx - worsty

#%% code for computing response profile
# compute for each matchup winrate of champion pool assuming generic pick rates
# and that the best champion for the matchup is always picked
def pool_winrates(champion_pool, role):
    # populate with winrates for best pick
    pool_winrates = {}

    for each_champion in champion_pool:
        # get codename and index associated with champion/role
        # for every matchup, check if entry for this matchup exists, 
        # and update it if winrate is higher
        champ_index = champion_index(each_champion, role)
        for i in range(len(winrates[champ_index])):
            opponent = champions[champ_index][i]
            winrate = float(winrates[champ_index][i])
            if opponent not in pool_winrates:
                pool_winrates[opponent] = winrate
            elif winrate > pool_winrates[opponent]:
                pool_winrates[opponent] = winrate

    return pool_winrates

# pool_winrates normalized by pick rate of opposing champion
def normalized_pool_winrates(champion_pool, role):
    # start by finding pool winrates
    pw = pool_winrates(champion_pool, role)
    matchups = list(pw.keys())

    # for each champion mentioned in keys, find its playrate
    raw = []
    for matchup in matchups:
        # find its code name and use it to seek its play rate
        champ_index = champion_index(matchup, role)
        raw.append(pickrates[champ_index])

    # normalize playrate vector
    s = sum(raw)
    norm = [float(i)/s for i in raw]

    # weighted mean using playrate vector
    for i in range(len(matchups)):
        pw[matchups[i]] = (pw[matchups[i]] * norm[i])

    return pw

# performance score is the mean normalized pool winrate
# the best champion pools win the most against the most popular picks
def performance_score(champion_pool, role):
    return sum(normalized_pool_winrates(champion_pool, role).values())

# %% helper functions - get list of champions in a role
def all_champs(role):
    pool = []
    for name in codenames:
        if name.count('\t' + role) > 0:
            pool.append(names[name])
    return pool

def midlaners():
    return all_champs('mid')

def toplaners():
    return all_champs('top')

def adcs():
    return all_champs('adc')

def junglers():
    return all_champs('jungle')

def supports():
    return all_champs('support')

# %% misc helper functions
def champion_index(champion_name, role):
    if champion_name.lower() == 'twistedfate':
        champion_name = 'twisted fate'
    if champion_name.lower() == "aurelionsol":
        champion_name = 'aurelion sol'
    if champion_name.lower() == "velkoz":
        champion_name = "vel'koz"
    if champion_name.lower() == 'monkeyking':
        champion_name = 'wukong'
    if champion_name.lower() == 'chogath':
        champion_name = "cho'gath"
    if champion_name.lower() == 'tahmkench':
        champion_name = "tahm kench"
    if champion_name.lower() == 'jarvaniv':
        champion_name = "jarvan iv"
    if champion_name.lower() == 'drmundo':
        champion_name = 'dr. mundo'
    if champion_name.lower() == 'xinzhao':
        champion_name = 'xin zhao'
    if champion_name.lower() == 'leesin':
        champion_name = 'lee sin'
    if champion_name.lower() == 'khazix':
        champion_name = "kha'zix"
    if champion_name.lower() == 'reksai':
        champion_name = "rek'sai"
    if champion_name.lower() == 'masteryi':
        champion_name = "master yi"
    if champion_name.lower() == 'missfortune':
        champion_name = "miss fortune"
    if champion_name.lower() == 'kogmaw':
        champion_name = "Kog'Maw"
    codename = rnames[champion_name.lower()]
    codename = codename[:codename.find('\t')] + '\t' + role
    return codenames.index(codename)

# sort first list by values in second list
def sort_names_by_values(X, Y):
    return [x for (y, x) in sorted(zip(Y, X), key=lambda pair: pair[0])]

# %% wrapper functions
# get worst_winrates for a given role
def role_worst_winrates(role):
    return worst_winrates_single(all_champs(role), role)

def sorted_pool_winrates(champion_pool, role):
    pw = pool_winrates(champion_pool, role)
    return sort_names_by_values(pw.keys(), pw.values()), sorted(pw.values())

def print_sorted_pool_winrates(champion_pool, role):
    a = sorted_pool_winrates(champion_pool, role)
    for i in range(len(a[0])):
        print (a[0][i] + '\t' + str(a[1][i]))

def store_role_worst_winrates(role):
    output = open(role + 'worstwinrates.txt', 'a')
    a = role_worst_winrates(role)
    for i in range(len(a[0])):
        output.write(a[0][i] + '\t' + str(a[1][i]) + '\n')
    output.close()

# %% now i need a function that list champions to potentially add to a pool
# based on worst_winrates_pool
def recommend_by_worst(champion_pool, role):
    rolechamps = all_champs(role)
    recs = []
    for each in champion_pool:
        del rolechamps[rolechamps.index(each)]
    for i in range(len(rolechamps)):
        if champion_pool.count(rolechamps[i]) > 0:
            print( rolechamps[i])
            continue
        recs.append(worst_winrate_pool(champion_pool + [rolechamps[i]], role))
    return list(reversed(sort_names_by_values(rolechamps, recs))), list(reversed(sorted(recs)))

# based on performance score
def recommend_by_performance_score(champion_pool, role):
    rolechamps = all_champs(role)
    recs = []
    for each in champion_pool:
        del rolechamps[rolechamps.index(each)]
    for i in range(len(rolechamps)):
        recs.append(performance_score(champion_pool + [rolechamps[i]], role))
    return list(reversed(sort_names_by_values(rolechamps, recs))), list(reversed(sorted(recs)))

# %% similar but this time i want to recommend removing champions from the pool
# taking pool and role
def remove_by_worst(champion_pool, role):
    recs = []
    for i in range(len(champion_pool)):
        recs.append(
                worst_winrate_pool(
                        champion_pool[:i] + champion_pool[i+1:], role))
    return sort_names_by_values(champion_pool, recs), sorted(recs)

# based on performance score
def remove_by_performance_score(champion_pool, role):
    recs = []
    for i in range(len(champion_pool)):
        recs.append(
                performance_score(
                        champion_pool[:i] + champion_pool[i+1:], role))
    return sort_names_by_values(champion_pool, recs), sorted(recs)

def output(role, champion_pool):
    try:
        output = ''
        output += 'Role: ' + role.upper() +'\n'
        output += 'Champion Pool: ' + str(champion_pool) + '\n'
        output += "\nSafety Summary.\nWinrate of each champion in pool when they're in their worst matchup:\n"
        output += str(worst_winrates_single(champion_pool, role)) + '\n'
        output += """\nResponse Summary: How responsive is your champion pool?
    If you get the chance, can you counter or match any opposing pick?
    THis is your worst possible matchup winrate supposing you always get to counterpick
    and always pick the champion in your pool with the best winrate for the matchup:\n"""
        output += str(worst_winrate_pool(champion_pool, role)) + '\n'
        output += """\nPerformance Summary:
    What's your average matchup winrate if you always get to pick the champion in your pool with the best matchup against the opposing pick?\n"""
        output += str(performance_score(champion_pool, role)) + '\n'
        output += """\nRecommendations: 
    Using either worst_winrate_pool() or performance_score() to score, rank champions by what they'd improve your score to if they were added to your champion pool.\n"""
        output += "\nRecommendation by performance score: " + str(recommend_by_performance_score(champion_pool, role)) +'\n'
        output += "\nRecommendation by worst matchup score: " + str(recommend_by_worst(champion_pool, role))
    except ValueError:
        output = "Something about your input is invalid. Maybe you've mispelled a role or champion name, made a formatting mistake, or mismatched a champion to role they aren't played in. Try again!"
    return output

# app organization
@app.route("/", methods=['GET', 'POST'])
def hello():
    form = ReusableForm(request.form)
 
    print(form.errors)
    if request.method == 'POST':
        role=request.form['role'].lower()
        champion_pool=request.form['champions'].split(', ')
        for i in range(len(champion_pool)):
            champion_pool[i] = champion_pool[i].title()
 
        if (
            role == 'top' or role == 'mid' or role == 'jungle' or role == 'adc' or role == 'support'
        ) and (
            len(champion_pool) != 0
        ):
            # Save the comment here.
            for each in output(role, champion_pool).split('\n'):
                flash(each)
        else:
            flash('Error: All the form fields are required and must be formatted correctly. ')
 
    return render_template('hello.html', form=form)
 
if __name__ == "__main__":
    app.run()
