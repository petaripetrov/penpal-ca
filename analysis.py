import pandas as pd
import scipy.stats as stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
import os

# Set path (update as needed)
path = "data"

# WORD RETENTION TEST ANALYSIS
def load_data(language):
    memory_df = pd.read_csv(os.path.join(path, f"Memory-{language}.csv"))
    no_memory_df = pd.read_csv(os.path.join(path, f"No-memory-{language}.csv"))
    
    memory_df['condition'] = 'memory'
    no_memory_df['condition'] = 'no_memory'

    memory_df.columns = memory_df.columns.str.strip()
    no_memory_df.columns = no_memory_df.columns.str.strip()

    # if you download the full excel and use python to convert to csv, the scores/10 will become their scores automatically
    # memory_df['Score'] = memory_df['Score'].astype(str).apply(convert_score)
    # no_memory_df['Score'] = no_memory_df['Score'].astype(str).apply(convert_score)

    # Drop any column that is entirely empty
    memory_df.dropna(axis=1, how='all', inplace=True)
    no_memory_df.dropna(axis=1, how='all', inplace=True)
    
    memory_df = memory_df[['Please enter your participant ID', 'Score', 'condition']]
    no_memory_df = no_memory_df[['Please enter your participant ID', 'Score', 'condition']]
    
    return pd.concat([memory_df, no_memory_df])

def convert_score(score):
    try:
        num, denom = map(int, score.split('/'))
        return num / denom
    except:
        return None

def test_word_recall(language, data):
    no_memory = data[data['condition'] == 'no_memory']['Score']
    memory = data[data['condition'] == 'memory']['Score']
    
    if stats.shapiro(no_memory)[1] > 0.05 and stats.shapiro(memory)[1] > 0.05:
        t_stat, p_value = stats.ttest_rel(no_memory, memory)
        test_used = "Paired t-test"
    else:
        t_stat, p_value = stats.wilcoxon(no_memory, memory)
        test_used = "Wilcoxon signed-rank test"
    
    print(f"{language}: {test_used}: Statistic={t_stat}, p-value={p_value}")

languages = ['French', 'Spanish']
for lang in languages:
    data = load_data(lang)
    test_word_recall(lang, data)

# ENGAGEMENT SURVEY ANALYSIS
def convert_likert_response(response):
    mapping = {
        "Strongly Disagree": 1,
        "Disagree": 2,
        "Neither agree nor disagree": 3,
        "Agree": 4,
        "Strongly agree": 5
    }
    return mapping.get(response, None)

def load_engagement_data():
    engagement_df = pd.read_csv(os.path.join(path, "Survey.csv"))

    # If any cell is empty, drop the entire row
    engagement_df.dropna(how='any', inplace=True)
    
    engagement_columns = engagement_df.columns[5:17]
    for col in engagement_columns:
        engagement_df[col] = engagement_df[col].apply(convert_likert_response)

    memory_df = engagement_df[engagement_df['Memory'] == 'Yes']
    no_memory_df = engagement_df[engagement_df['Memory'] == 'No']
    
    return memory_df, no_memory_df

def test_user_engagement():
    memory_df, no_memory_df = load_engagement_data()
    engagement_columns = memory_df.columns[5:17]
    
    for col in engagement_columns:
        merged_df = pd.merge(memory_df[['Please enter your participant ID', col]], no_memory_df[['Please enter your participant ID', col]], on='Please enter your participant ID', suffixes=('_memory', '_no_memory'))
        
        # Drop rows with NaN values in either column
        memory_scores = merged_df[col + '_memory'].dropna()
        no_memory_scores = merged_df[col + '_no_memory'].dropna()
        
        stat, p_value = stats.wilcoxon(memory_scores, no_memory_scores)

        print(f"{col}: Wilcoxon signed-rank test: Statistic={stat}, p-value={p_value}")

test_user_engagement()

# TO-DO: ANOVA
