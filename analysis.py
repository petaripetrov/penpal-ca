import pandas as pd
import scipy.stats as stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
import os
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import re

# Set path (update as needed)
path = "data"

word_recall_results = []
engagement_results = []

# DATA PROCESSING
def replace_missing_rows(memory_df, no_memory_df):

    memory_ids = set(memory_df['Please enter your participant ID'])
    no_memory_ids = set(no_memory_df['Please enter your participant ID'])

    # Find unmatched IDs
    only_in_memory = memory_ids - no_memory_ids
    only_in_no_memory = no_memory_ids - memory_ids

    # Fill in missing no_memory rows
    for pid in only_in_memory:
        avg_score = no_memory_df['Score'].mean()
        fake_row = pd.DataFrame([{
            'Please enter your participant ID': pid,
            'Score': avg_score,
            'Memory': 1
        }])
        no_memory_df = pd.concat([no_memory_df, fake_row], ignore_index=True)

    # Fill in missing memory rows
    for pid in only_in_no_memory:
        avg_score = memory_df['Score'].mean()
        fake_row = pd.DataFrame([{
            'Please enter your participant ID': pid,
            'Score': avg_score,
            'Memory': 0
        }])
        memory_df = pd.concat([memory_df, fake_row], ignore_index=True)

    return memory_df, no_memory_df

def remove_missing_rows(memory_df,no_memory_df):
    common_ids = set(memory_df['Please enter your participant ID']).intersection(
        no_memory_df['Please enter your participant ID']
    )

    memory_df = memory_df[memory_df['Please enter your participant ID'].isin(common_ids)]
    no_memory_df = no_memory_df[no_memory_df['Please enter your participant ID'].isin(common_ids)]

    return memory_df, no_memory_df

def count_languages(text):
    if not isinstance(text, str):
        return 0  # Handle non-string values gracefully
    
    # Clean the text by removing unnecessary words and phrases
    cleaned_text = re.sub(r'\b(native|a bit of|a bit|is my native langauge|is my|is|and some|and|language)\b', '', text, flags=re.IGNORECASE)
    
    # Replace hyphens with spaces to avoid splitting valid language names
    cleaned_text = cleaned_text.replace('-', ' ')
    
    # Split the text into individual languages using commas, spaces, or other delimiters
    languages = [lang.strip() for lang in re.split(r'[,\s]+', cleaned_text) if lang.strip()]
    
    # Return the count of unique languages
    return len(languages)


# LOAD DATA
def load_data(language):
    memory_df = pd.read_csv(os.path.join(path, f"Memory-{language}.csv"))
    no_memory_df = pd.read_csv(os.path.join(path, f"No-memory-{language}.csv"))
    
    memory_df['Memory'] = 1 # Assign 1 for memory 
    no_memory_df['Memory'] = 0 # Assign 0 for no memory

    memory_df.columns = memory_df.columns.str.strip()
    no_memory_df.columns = no_memory_df.columns.str.strip()

    # Drop any column that is entirely empty
    memory_df.dropna(axis=1, how='all', inplace=True)
    no_memory_df.dropna(axis=1, how='all', inplace=True)
    
    memory_df = memory_df[['Please enter your participant ID', 'Score', 'Memory']]
    no_memory_df = no_memory_df[['Please enter your participant ID', 'Score', 'Memory']]
    
    # # Remove any rows with empty participant IDs
    # memory_df, no_memory_df = remove_missing_rows(memory_df, no_memory_df)

    # Replace missing rows with average scores
    memory_df, no_memory_df = replace_missing_rows(memory_df, no_memory_df)

    return pd.concat([memory_df, no_memory_df])

def load_data_all_languages(languages):
    all_data = []
    for lang in languages:
        # load_data now already replaces missing rows with average scores
        data = load_data(lang)
        data['Language'] = lang  # add a column for language
        data = data.rename(columns={"Please enter your participant ID": "ID"})
        all_data.append(data)
    return pd.concat(all_data, ignore_index=True)

def load_engagement_data():
    engagement_df = pd.read_csv(os.path.join(path, "Survey.csv"))

    # If any cell is empty, drop the entire row
    engagement_df.dropna(how='any', inplace=True)
    
    engagement_columns = engagement_df.columns[5:17]
    for col in engagement_columns:
        engagement_df[col] = engagement_df[col].apply(convert_likert_response)

    memory_df = engagement_df[engagement_df['Memory'] == 'Yes']
    no_memory_df = engagement_df[engagement_df['Memory'] == 'No']

    # map memory condition to 1 and no memory condition to 0
    memory_df['Memory'] = memory_df['Memory'].map({'Yes': 1, 'No': 0})
    no_memory_df['Memory'] = no_memory_df['Memory'].map({'Yes': 1, 'No': 0})

    return memory_df, no_memory_df

# PLOTTING
def plot_word_recall_scores(language):
    memory_df = pd.read_csv(os.path.join(path, f"Memory-{language}.csv"))
    no_memory_df = pd.read_csv(os.path.join(path, f"No-memory-{language}.csv"))

    memory_df['condition'] = 'memory'
    no_memory_df['condition'] = 'no_memory'

    memory_df.columns = memory_df.columns.str.strip()
    no_memory_df.columns = no_memory_df.columns.str.strip()

    memory_df['Score'] = pd.to_numeric(memory_df['Score'], errors='coerce')
    no_memory_df['Score'] = pd.to_numeric(no_memory_df['Score'], errors='coerce')

    df = pd.concat([memory_df[['Please enter your participant ID', 'Score', 'condition']],
                    no_memory_df[['Please enter your participant ID', 'Score', 'condition']]])

    os.makedirs("plots/recall", exist_ok=True)

    # Distribution Plot
    plt.figure(figsize=(8, 5))
    sns.histplot(data=df, x='Score', hue='condition', kde=True, palette='pastel', element='step')
    plt.title(f"{language} - Score Distribution")
    plt.savefig(f"plots/recall/{language}_score_distribution.png")
    plt.close()

def plot_engagement():
    memory_df, no_memory_df = load_engagement_data()
    
    engagement_columns = memory_df.columns[5:17]
    
    long_data = []
    question_number = 1
    for col in engagement_columns:
        # For memory condition
        df_mem = memory_df[['Please enter your participant ID', col]].copy()
        df_mem['condition'] = 'memory'
        df_mem['Question'] = f"{question_number}"
        df_mem = df_mem.rename(columns={col: 'Score'})
        
        # For no_memory condition
        df_nomem = no_memory_df[['Please enter your participant ID', col]].copy()
        df_nomem['condition'] = 'no_memory'
        df_nomem['Question'] = f"{question_number}"
        df_nomem = df_nomem.rename(columns={col: 'Score'})
        
        long_data.append(df_mem)
        long_data.append(df_nomem)
        
        question_number += 1

    combined_long = pd.concat(long_data, ignore_index=True)
    
    combined_long['Score'] = pd.to_numeric(combined_long['Score'], errors='coerce')
    
    min_score = combined_long['Score'].min()
    max_score = combined_long['Score'].max()
    margin = 0.2
    y_min = min(1, min_score - margin)
    y_max = max(5, max_score + margin)

    os.makedirs("plots/engagement", exist_ok=True)
    
    # Create the grouped box plot
    plt.figure(figsize=(12, 6))
    ax = sns.boxplot(x='Question', y='Score', hue='condition', data=combined_long, palette="pastel")
    plt.title("User Engagement Scores on Likert Scale")
    plt.ylim(y_min, y_max) 
    plt.xlabel("Question")
    plt.ylabel("Score")
    plt.legend(title="Condition", loc="upper right")
    plt.tight_layout()
    plt.savefig("plots/engagement/engagement_boxplots.png")
    plt.close()

# WORD RETENTION TEST ANALYSIS
def test_word_recall(language, data):
    no_memory = data[data['Memroy'] == 0]['Score']
    memory = data[data['Memory'] == 1]['Score']

    # test for normality
    if stats.shapiro(no_memory)[1] > 0.05 and stats.shapiro(memory)[1] > 0.05:
        t_stat, p_value = stats.ttest_rel(no_memory, memory)
        test_used = "Paired t-test"
    else:
        t_stat, p_value = stats.wilcoxon(no_memory, memory)
        test_used = "Wilcoxon signed-rank test"

    print(f"{language}: {test_used}: Statistic={t_stat}, p-value={p_value}")
    word_recall_results.append({
        'Language': language,
        'Test': test_used,
        'Statistic': t_stat,
        'p-value': p_value
    })

def test_word_recall_individual():
    languages = ["Spanish", "French", "Japanese", "German"]
    for lang in languages:
        data = load_data(lang)
        test_word_recall(lang, data)
        plot_word_recall_scores(lang)

def measure_word_recall_all_languages():
    languages = ["Spanish", "French", "Japanese", "German"]
    all_data = load_data_all_languages(languages)
    print(all_data.columns)

    # save all data to CSV
    all_data.to_csv("output/recall_all_languages.csv", index=False)

    all_data['Score'] = pd.to_numeric(all_data['Score'], errors='coerce')
    all_data.dropna(subset=['Score'], inplace=True)

    print(all_data['Score'].describe())

    # Fit the mixed-effects model:
    # Score ~ condition is our fixed effect
    # groups=Language tells the model to use language as a random intercept
    model = smf.mixedlm("Score ~ C(condition)", data=all_data, groups=all_data["Language"])
    model_fit = model.fit()

    print(model_fit.summary())

    # save the model summary to a CSV file
    with open("output/recall_mixed_effects_model_summary.txt", "w") as f:
        f.write(str(model_fit.summary()))

    sns.violinplot(data=all_data, x="Language", y="Score", hue="condition", split=True, palette="pastel")
    plt.title("Word Recall Scores by Language and Condition")
    plt.savefig("plots/recall/violin_distr.png")
    plt.show()
    plt.close()

def analyze_background_effects_on_word_recall():
    # 1. Load the survey data
    survey_df = pd.read_csv(os.path.join(path, "Survey.csv"))
    
    survey_df.columns = survey_df.columns.str.strip()

    survey_info = survey_df[[
        'Please enter your participant ID',
        'What languages are you familiar with?',
        'Do you have experience with language learning?',
        'Have you used conversational assistants or language-learning chatbots?'
    ]].copy()

    # Clean column names
    survey_info.columns = ['ID', 'NumLanguages', 'PriorExperience', 'CAFamiliarity']

    survey_info['PriorExperience'] = survey_info['PriorExperience'].map({'Yes': 1, 'No': 0})
    survey_info['CAFamiliarity'] = survey_info['CAFamiliarity'].map({'Yes': 1, 'No': 0})
    # convert the strings of languages into a count using regex function above
    survey_info['NumLanguages'] = survey_info['NumLanguages'].apply(count_languages)

    # drop duplicates as participants filled in this part twice but entries didnt change
    survey_info = survey_info.drop_duplicates(subset=['ID'])

    # load the word recall data
    word_recall_data = load_data_all_languages(["Spanish", "French", "Japanese", "German"])
    
    # merge the two dataframes on 'ID'
    merged = pd.merge(word_recall_data, survey_info, on='ID')

    # fit mixed-effects model
    model = smf.mixedlm(
        "Score ~ Memory * NumLanguages + PriorExperience + CAFamiliarity",  # Confounding variables
        data=merged,
        groups=merged["ID"],  # Random effect for repeated measures
    )
    result = model.fit()
    print(result.summary())

    # save the model summary to a CSV file
    with open("output/recall_background_effects_summary.txt", "w") as f:
        f.write(str(result.summary()))

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

def test_user_engagement():
    memory_df, no_memory_df = load_engagement_data()
    engagement_columns = memory_df.columns[5:17]
    
    for col in engagement_columns:
        merged_df = pd.merge(memory_df[['Please enter your participant ID', col]], no_memory_df[['Please enter your participant ID', col]], on='Please enter your participant ID', suffixes=('_memory', '_no_memory'))

        memory_scores = merged_df[col + '_memory'].dropna() # fix this
        no_memory_scores = merged_df[col + '_no_memory'].dropna()

        stat, p_value = stats.wilcoxon(memory_scores, no_memory_scores)

        print(f"{col}: Wilcoxon signed-rank test: Statistic={stat}, p-value={p_value}")
        engagement_results.append({
            'Question': col,
            'Test': 'Wilcoxon signed-rank test',
            'Statistic': stat,
            'p-value': p_value
        })

if __name__ == "__main__":
    test_word_recall_individual()

    # test_user_engagement()
    # plot_engagement()

    pd.DataFrame(word_recall_results).to_csv("output/word_recall_results.csv", index=False)
    pd.DataFrame(engagement_results).to_csv("output/engagement_results.csv", index=False)

    measure_word_recall_all_languages()

    analyze_background_effects_on_word_recall()




