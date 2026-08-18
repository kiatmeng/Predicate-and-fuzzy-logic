import pandas as pd
import numpy as np

# ==============================================================================
# 1.0 Load Heterogeneous Datasets
# ==============================================================================
df_a = pd.read_excel('dataset/BTIS3043_Dataset_A_Existing_eBook_Collection.xlsx')
df_b = pd.read_excel('dataset/BTIS3043_Dataset_B_Academic_eBook_Catalogue.xlsx')
df_c = pd.read_excel('dataset/BTIS3043_Dataset_C_eBook_Acquisition_Catalogue.xlsx')

# ==============================================================================
# 2.0 Define Scenario Keywords & Combined Text Fields (Aligned with Report)
# ==============================================================================
ai_kw = ['artificial intelligence', 'machine learning', 'intelligent systems', 'computer vision', 'robotics', 'expert system', 'knowledge representation']
prog_kw = ['programming', 'python', 'java', 'c\+\+', 'algorithm', 'data structure', 'software engineering']
math_kw = ['mathematics', 'statistics', 'probability', 'linear algebra', 'discrete math', 'calculus', 'optimization', 'decision analysis']
s1_keywords = ai_kw + prog_kw + math_kw

sec_kw = ['cybersecurity', 'computer security', 'network security', 'cryptography', 'privacy', 'digital forensics', 'information assurance', 'secure systems', 'secure computing', 'information security', 'security in computing']

# ① Dataset B: 组合 Discipline Levels 1–4 字段（满足 Report 3.3 与 4.3 描述）
df_b['Discipline_Full'] = df_b[['Discipline (Level 1)', 'Discipline (Level 2)', 'Discipline (Level 3)', 'Discipline (Level 4)']].fillna('').agg(' / '.join, axis=1)

# ② Dataset C: 组合 Category + Discipline + Title 字段（满足 Report 3.4 与 4.4 描述）
df_c['Text_Full'] = df_c[['Category', 'Discipline', 'Title']].fillna('').agg(' '.join, axis=1)

# Scenario 1 分类函数（生成题目要求的 Identified Role 标签）
def categorize_s1(title, disc='', cat=''):
    text = str(title).lower() + ' ' + str(disc).lower() + ' ' + str(cat).lower()
    if any(k in text for k in ai_kw): 
        return 'Direct AI'
    elif any(k.replace('\\', '') in text for k in prog_kw): 
        return 'Programming Support'
    elif any(k in text for k in math_kw): 
        return 'Mathematical Support'
    return 'Other Justified'

# ==============================================================================
# 3.0 Fuzzy Membership Functions (Report Table 2 & Section 4)
# ==============================================================================
def fuzzy_recency(year):
    """Publication recency mapping (2014 to >=2024 -> 0.0 to 1.0)"""
    try:
        y = int(year)
        if y >= 2024: return 1.0
        elif y <= 2014: return 0.0
        else: return (y - 2014) / 10.0
    except:
        return 0.0

def fuzzy_affordability(price):
    """Price affordability mapping (<=100 to >=400 -> 1.0 to 0.0)"""
    try:
        p = float(price)
        if pd.isna(p): return 0.0
        if p <= 100: return 1.0
        elif p >= 400: return 0.0
        else: return (400 - p) / 300.0
    except:
        return 0.0

# --- Scenario 1 Specific Fuzzy Functions ---
def fuzzy_relevance_s1(role):
    """Topic Relevance: Direct AI (1.0) > Programming / Math Support (0.75) > Others (0.25)"""
    if role == 'Direct AI': 
        return 1.0
    elif role in ['Programming Support', 'Mathematical Support']: 
        return 0.75
    else: 
        return 0.25

def fuzzy_discipline_s1(disc_str):
    """Discipline match strength across Levels 1–4 / Categories"""
    disc_str = str(disc_str).lower()
    if any(k in disc_str for k in ai_kw) or 'intelligence' in disc_str: 
        return 1.0
    elif any(k.replace('\\', '') in disc_str for k in prog_kw) or 'comput' in disc_str or 'it' in disc_str or 'engineering' in disc_str: 
        return 0.75
    elif any(k in disc_str for k in math_kw) or 'math' in disc_str or 'stat' in disc_str: 
        return 0.75
    else: 
        return 0.25

# --- Scenario 2 Specific Fuzzy Functions ---
def fuzzy_relevance_s2(title, disc='', cat=''):
    """Topic Relevance for Cybersecurity (2+ hits -> 1.0, 1 hit -> 0.75, general -> 0.25)"""
    text = str(title).lower() + ' ' + str(disc).lower() + ' ' + str(cat).lower()
    matches = sum(1 for k in sec_kw if k in text)
    if matches >= 2: return 1.0
    elif matches == 1: return 0.75
    else: return 0.25

def fuzzy_discipline_s2(disc_str, keywords):
    """Discipline match strength for Security topics"""
    disc_str = str(disc_str).lower()
    if any(k.replace('\\', '') in disc_str for k in keywords): return 1.0
    elif 'comput' in disc_str or 'security' in disc_str or 'it' in disc_str: return 0.75
    else: return 0.5

# --- Common Metadata Functions ---
def fuzzy_recommendation(rec_str):
    return 1.0 if 'CS/IT' in str(rec_str) else 0.5

def fuzzy_format(fmt_str):
    return 1.0 if 'ePub' in str(fmt_str) or 'PDF' in str(fmt_str) else 0.5


# ==============================================================================
# 5.0 FIXED SCENARIO 1: AI, Programming and Mathematical Foundations
# ==============================================================================
print("\n" + "="*90)
print("5.0 FIXED SCENARIO 1: Artificial Intelligence, Programming and Mathematical Foundations")
print("="*90)
LIMIT_S1 = 5

# ----------------- Dataset A (Existing Collection) -----------------
print("\n[ DATASET A: Existing Collection ]")
cond_a = df_a['Title'].str.lower().str.contains('|'.join(s1_keywords), na=False) & (df_a['Quantity'] > 0)
res_a = df_a[cond_a].copy()

if res_a.empty:
    print("Explanation: Fewer than 5 records found because Dataset A is extremely small (9 records) and lacks direct titles.")
else:
    res_a['Identified Role'] = res_a['Title'].apply(categorize_s1)
    total_a = len(res_a)
    
    print("\n--> STEP 1: PREDICATE-ONLY RESULTS (Unranked)")
    disp1_a = res_a[['Title', 'Copyright Year', 'Identified Role']].head(LIMIT_S1).copy()
    disp1_a.index = range(1, len(disp1_a) + 1)
    print(disp1_a.to_markdown(index=True))
    if total_a < LIMIT_S1:
        print(f"Explanation: Only {total_a} record found because Dataset A is extremely small (9 records) and focuses mainly on Electrical Circuits/Accounting.")

    res_a['Fz_Rel'] = res_a['Identified Role'].apply(fuzzy_relevance_s1)
    res_a['Fz_Rec'] = res_a['Copyright Year'].apply(fuzzy_recency)
    res_a['Fz_Recmd'] = res_a['Recommended by'].apply(fuzzy_recommendation)
    res_a['Fz_Aff'] = res_a['Unit Net Price'].apply(fuzzy_affordability)
    res_a['Overall_FzScore'] = (res_a['Fz_Rel'] + res_a['Fz_Rec'] + res_a['Fz_Recmd'] + res_a['Fz_Aff']) / 4
    
    print("\n--> STEP 2: INDIVIDUAL FUZZY SCORES (Unranked)")
    disp2_a = res_a[['Title', 'Fz_Rel', 'Fz_Rec', 'Fz_Recmd', 'Fz_Aff']].head(LIMIT_S1).copy()
    disp2_a.index = range(1, len(disp2_a) + 1)
    print(disp2_a.to_markdown(index=True))
    
    print("\n--> STEP 3: OVERALL RANKED RESULTS (Max 5)")
    res_a_sorted = res_a.sort_values('Overall_FzScore', ascending=False)
    disp3_a = res_a_sorted[['Title', 'Copyright Year', 'Identified Role', 'Overall_FzScore']].head(LIMIT_S1).copy()
    disp3_a.index = [f"Top {i+1}" for i in range(len(disp3_a))]
    print("-> Price Field Used for Affordability: 'Unit Net Price'")
    print(disp3_a.to_markdown(index=True))

# ----------------- Dataset B (Discipline Levels 1–4) -----------------
print("\n\n[ DATASET B: Academic Catalogue ]")
cond_b = df_b['Title'].str.lower().str.contains('|'.join(s1_keywords), na=False) | df_b['Discipline_Full'].str.lower().str.contains('|'.join(s1_keywords), na=False)
res_b = df_b[cond_b].copy()
res_b['Identified Role'] = res_b.apply(lambda row: categorize_s1(row['Title'], row['Discipline_Full']), axis=1)
total_b = len(res_b)

print("\n--> STEP 1: PREDICATE-ONLY RESULTS (Unranked)")
# 显示完整的 Discipline Levels 1–4
disp1_b = res_b[['Title', 'Copyright', 'Discipline_Full', 'Identified Role']].head(LIMIT_S1).copy()
disp1_b.index = range(1, len(disp1_b) + 1)
print(disp1_b.to_markdown(index=True))
if total_b > LIMIT_S1: print(f"    ... and {total_b - LIMIT_S1} more records passed the predicate filter.")

res_b['Fz_Rel'] = res_b['Identified Role'].apply(fuzzy_relevance_s1)
res_b['Fz_Disc'] = res_b['Discipline_Full'].apply(fuzzy_discipline_s1)
res_b['Fz_Rec'] = res_b['Copyright'].apply(fuzzy_recency)
res_b['Overall_FzScore'] = (res_b['Fz_Rel'] + res_b['Fz_Disc'] + res_b['Fz_Rec']) / 3

print("\n--> STEP 2: INDIVIDUAL FUZZY SCORES (Unranked)")
disp2_b = res_b[['Title', 'Fz_Rel', 'Fz_Disc', 'Fz_Rec']].head(LIMIT_S1).copy()
disp2_b.index = range(1, len(disp2_b) + 1)
print(disp2_b.to_markdown(index=True))
if total_b > LIMIT_S1: print(f"    ... and {total_b - LIMIT_S1} more records evaluated.")

print("\n--> STEP 3: OVERALL RANKED RESULTS (Max 5)")
res_b_sorted = res_b.sort_values('Overall_FzScore', ascending=False)
# 显示完整的 Discipline Levels 1–4
disp3_b = res_b_sorted[['Title', 'Copyright', 'Discipline_Full', 'Identified Role', 'Overall_FzScore']].head(LIMIT_S1).copy()
disp3_b.index = [f"Top {i+1}" for i in range(len(disp3_b))]
print(disp3_b.to_markdown(index=True))

# ----------------- Dataset C (Category + Discipline + Title) -----------------
print("\n\n[ DATASET C: Acquisition Catalogue ]")
cond_c = df_c['Text_Full'].str.lower().str.contains('|'.join(s1_keywords), na=False)
res_c = df_c[cond_c].copy()
res_c['Identified Role'] = res_c.apply(lambda row: categorize_s1(row['Title'], row['Discipline'], row['Category']), axis=1)
total_c = len(res_c)

print("\n--> STEP 1: PREDICATE-ONLY RESULTS (Unranked)")
disp1_c = res_c[['Title', 'Copyright Year', 'Category', 'Discipline', 'Identified Role']].head(LIMIT_S1).copy()
disp1_c.index = range(1, len(disp1_c) + 1)
print(disp1_c.to_markdown(index=True))
if total_c > LIMIT_S1: print(f"    ... and {total_c - LIMIT_S1} more records passed the predicate filter.")

res_c['Fz_Rel'] = res_c['Identified Role'].apply(fuzzy_relevance_s1)
res_c['Fz_Rec'] = res_c['Copyright Year'].apply(fuzzy_recency)
res_c['Fz_Disc'] = res_c['Discipline'].apply(fuzzy_discipline_s1)
res_c['Fz_Fmt'] = res_c['eBook Format'].apply(fuzzy_format)
res_c['Overall_FzScore'] = (res_c['Fz_Rel'] + res_c['Fz_Rec'] + res_c['Fz_Disc'] + res_c['Fz_Fmt']) / 4

print("\n--> STEP 2: INDIVIDUAL FUZZY SCORES (Unranked)")
disp2_c = res_c[['Title', 'Fz_Rel', 'Fz_Rec', 'Fz_Disc', 'Fz_Fmt']].head(LIMIT_S1).copy()
disp2_c.index = range(1, len(disp2_c) + 1)
print(disp2_c.to_markdown(index=True))
if total_c > LIMIT_S1: print(f"    ... and {total_c - LIMIT_S1} more records evaluated.")

print("\n--> STEP 3: OVERALL RANKED RESULTS (Max 5)")
res_c_sorted = res_c.sort_values('Overall_FzScore', ascending=False)
disp3_c = res_c_sorted[['Title', 'Copyright Year', 'Category', 'Discipline', 'Identified Role', 'Overall_FzScore']].head(LIMIT_S1).copy()
disp3_c.index = [f"Top {i+1}" for i in range(len(disp3_c))]
print("-> Note: Based on Section 4.4 parameters, price was not selected as a fuzzy attribute for Dataset C.")
print(disp3_c.to_markdown(index=True))


# ==============================================================================
# 6.0 FIXED SCENARIO 2: Cybersecurity & Secure Computing
# ==============================================================================
print("\n\n" + "="*90)
print("6.0 FIXED SCENARIO 2: Cybersecurity and Secure Computing")
print("="*90)
LIMIT_S2 = 10

# ----------------- Dataset A (Current Subscriptions) -----------------
print("\n[ DATASET A: Existing Collection (Current Subscriptions) ]")
cond_a2 = df_a['Title'].str.lower().str.contains('|'.join(sec_kw), na=False) & (df_a['Recommended by'] == 'CS/IT')
res_a2 = df_a[cond_a2].copy()
total_a2 = len(res_a2)

if res_a2.empty:
    print("No relevant Current Subscriptions found.")
else:
    print("\n--> STEP 1: PREDICATE-ONLY RESULTS (Unranked)")
    disp1_a2 = res_a2[['Title', 'Copyright Year', 'Recommended by']].head(LIMIT_S2).copy()
    disp1_a2.index = range(1, len(disp1_a2) + 1)
    print(disp1_a2.to_markdown(index=True))

    res_a2['Fz_Rel'] = res_a2.apply(lambda r: fuzzy_relevance_s2(r['Title']), axis=1)
    res_a2['Fz_Rec'] = res_a2['Copyright Year'].apply(fuzzy_recency)
    res_a2['Fz_Recmd'] = res_a2['Recommended by'].apply(fuzzy_recommendation)
    res_a2['Fz_Aff'] = res_a2['Unit Net Price'].apply(fuzzy_affordability)
    res_a2['Overall_FzScore'] = (res_a2['Fz_Rel'] + res_a2['Fz_Rec'] + res_a2['Fz_Recmd'] + res_a2['Fz_Aff']) / 4
    
    print("\n--> STEP 2: INDIVIDUAL FUZZY SCORES (Unranked)")
    disp2_a2 = res_a2[['Title', 'Fz_Rel', 'Fz_Rec', 'Fz_Recmd', 'Fz_Aff']].head(LIMIT_S2).copy()
    disp2_a2.index = range(1, len(disp2_a2) + 1)
    print(disp2_a2.to_markdown(index=True))
    
    print("\n--> STEP 3: OVERALL RANKED RESULTS (All Current Subscriptions)")
    res_a2_sorted = res_a2.sort_values('Overall_FzScore', ascending=False)
    disp3_a2 = res_a2_sorted[['Title', 'Copyright Year', 'Unit Net Price', 'Overall_FzScore']].head(LIMIT_S2).copy()
    disp3_a2.index = [f"Top {i+1}" for i in range(len(disp3_a2))]
    print("-> Price Field Used for Affordability: 'Unit Net Price'")
    print(disp3_a2.to_markdown(index=True))

# ----------------- Dataset B (Discipline Levels 1–4) -----------------
print("\n\n[ DATASET B: Academic Catalogue ]")
cond_b2 = df_b['Title'].str.lower().str.contains('|'.join(sec_kw), na=False) | df_b['Discipline_Full'].str.lower().str.contains('|'.join(sec_kw), na=False)
res_b2 = df_b[cond_b2].copy()
total_b2 = len(res_b2)

print("\n--> STEP 1: PREDICATE-ONLY RESULTS (Unranked)")
# 显示完整的 Discipline Levels 1–4
disp1_b2 = res_b2[['Title', 'Copyright', 'Discipline_Full']].head(LIMIT_S2).copy()
disp1_b2.index = range(1, len(disp1_b2) + 1)
print(disp1_b2.to_markdown(index=True))

res_b2['Fz_Rel'] = res_b2.apply(lambda r: fuzzy_relevance_s2(r['Title'], r['Discipline_Full']), axis=1)
res_b2['Fz_Disc'] = res_b2['Discipline_Full'].apply(lambda x: fuzzy_discipline_s2(x, sec_kw))
res_b2['Fz_Rec'] = res_b2['Copyright'].apply(fuzzy_recency)
res_b2['Overall_FzScore'] = (res_b2['Fz_Rel'] + res_b2['Fz_Disc'] + res_b2['Fz_Rec']) / 3

print("\n--> STEP 2: INDIVIDUAL FUZZY SCORES (Unranked)")
disp2_b2 = res_b2[['Title', 'Fz_Rel', 'Fz_Disc', 'Fz_Rec']].head(LIMIT_S2).copy()
disp2_b2.index = range(1, len(disp2_b2) + 1)
print(disp2_b2.to_markdown(index=True))

print("\n--> STEP 3: OVERALL RANKED RESULTS (Max 10)")
res_b2_sorted = res_b2.sort_values('Overall_FzScore', ascending=False)
# 显示完整的 Discipline Levels 1–4
disp3_b2 = res_b2_sorted[['Title', 'Copyright', 'Discipline_Full', 'Overall_FzScore']].head(LIMIT_S2).copy()
disp3_b2.index = [f"Top {i+1}" for i in range(len(disp3_b2))]
print(disp3_b2.to_markdown(index=True))

# ----------------- Dataset C (Category + Discipline + Title) -----------------
print("\n\n[ DATASET C: Acquisition Catalogue ]")
cond_c2 = df_c['Text_Full'].str.lower().str.contains('|'.join(sec_kw), na=False)
res_c2 = df_c[cond_c2].copy()
total_c2 = len(res_c2)

print("\n--> STEP 1: PREDICATE-ONLY RESULTS (Unranked)")
disp1_c2 = res_c2[['Title', 'Copyright Year', 'Category', 'Discipline']].head(LIMIT_S2).copy()
disp1_c2.index = range(1, len(disp1_c2) + 1)
print(disp1_c2.to_markdown(index=True))

res_c2['Fz_Rel'] = res_c2.apply(lambda r: fuzzy_relevance_s2(r['Title'], r['Discipline'], r['Category']), axis=1)
res_c2['Fz_Rec'] = res_c2['Copyright Year'].apply(fuzzy_recency)
res_c2['Fz_Disc'] = res_c2['Discipline'].apply(lambda x: fuzzy_discipline_s2(x, sec_kw))
res_c2['Fz_Fmt'] = res_c2['eBook Format'].apply(fuzzy_format)
res_c2['Overall_FzScore'] = (res_c2['Fz_Rel'] + res_c2['Fz_Rec'] + res_c2['Fz_Disc'] + res_c2['Fz_Fmt']) / 4

print("\n--> STEP 2: INDIVIDUAL FUZZY SCORES (Unranked)")
disp2_c2 = res_c2[['Title', 'Fz_Rel', 'Fz_Rec', 'Fz_Disc', 'Fz_Fmt']].head(LIMIT_S2).copy()
disp2_c2.index = range(1, len(disp2_c2) + 1)
print(disp2_c2.to_markdown(index=True))

print("\n--> STEP 3: OVERALL RANKED RESULTS (Max 10)")
res_c2_sorted = res_c2.sort_values('Overall_FzScore', ascending=False)
disp3_c2 = res_c2_sorted[['Title', 'Copyright Year', 'Category', 'Discipline', 'Overall_FzScore']].head(LIMIT_S2).copy()
disp3_c2.index = [f"Top {i+1}" for i in range(len(disp3_c2))]
print("-> Note: Based on Section 4.4 parameters, price was not selected as a fuzzy attribute for Dataset C.")
print(disp3_c2.to_markdown(index=True))