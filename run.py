import pandas as pd
import streamlit as st
import altair as alt
import os
import unicodedata

def normalize_text(text):
    if isinstance(text, str):
        return unicodedata.normalize('NFKC', text.strip())
    return text

# 设置页面标题
st.title("题目分析-数学")

# 自动读取当前目录下所有的xlsx文件
file_list = [f for f in os.listdir() if f.endswith('.xlsx')]

if file_list:
    selected_file = st.selectbox("请选择要统计的作业/考试:", file_list)
    df = pd.read_excel(selected_file)
    df.columns = df.columns.str.replace('试题 ', '试题', regex=False)

    teachers = df['教师'].unique()
    classes = df['班级'].unique()
    selected_teacher = st.selectbox("选择教师:", ["全部"] + list(teachers))
    
    if selected_teacher != "全部":
        filtered_classes = df[df['教师'] == selected_teacher]['班级'].unique()
    else:
        filtered_classes = classes

    selected_class = st.selectbox("选择班级:", ["全部"] + list(filtered_classes))
    
    if selected_teacher != "全部":
        df = df[df['教师'] == selected_teacher]
    if selected_class != "全部":
        df = df[df['班级'] == selected_class]
    
    results = []
    i = 1
    
    while True:
        answer_col = f'回答{i}'
        if answer_col not in df.columns:
            break

        df[answer_col] = df[answer_col].apply(normalize_text)
        standard_answer_col = f'标准答案{i}'
        df[standard_answer_col] = df[standard_answer_col].apply(normalize_text)
        
        standard_answer = df[standard_answer_col].iloc[0]
        valid_answers = df[answer_col].dropna()
        result = valid_answers.value_counts().reset_index()
        result.columns = ['答案', '出现次数']
        
        result['学生'] = result['答案'].apply(lambda x: ', '.join(df[df[answer_col] == x]['姓氏'].astype(str) + df[df[answer_col] == x]['名'].astype(str)))
        
        correct_count = (df[answer_col] == standard_answer).sum()
        total_count = df[answer_col].notna().sum()
        accuracy = (correct_count / total_count * 100) if total_count > 0 else 0
        
        answering_count = total_count
        question_content = df[f'试题{i}'].iloc[0]

        results.append({
            '题号': i,
            '试题': question_content,
            '标准答案': standard_answer,
            '答题人数': answering_count,
            '正确率': accuracy,
            '答案统计': result[['答案', '出现次数', '学生']],
            '错误答案统计': result[result['答案'] != standard_answer].sort_values(by='出现次数', ascending=False)
        })
        
        i += 1
    
    sort_option = st.selectbox("选择排序方式:", ["按照题目原本顺序", "按照正确率升序", "按照正确率降序"])
    
    if sort_option == "按照正确率升序":
        sorted_results = sorted(results, key=lambda x: x['正确率'])
    elif sort_option == "按照正确率降序":
        sorted_results = sorted(results, key=lambda x: x['正确率'], reverse=True)
    else:
        sorted_results = results
    
    st.sidebar.title("题目导航")
    for res in sorted_results:
        question_link = f"[第{res['题号']}题 (正确率: {res['正确率']:.2f}%)](#{res['题号']})"
        st.sidebar.markdown(question_link)
    
    for res in sorted_results:
        st.markdown(f"<a id='{res['题号']}'></a>", unsafe_allow_html=True)
        st.subheader(f"第{res['题号']}题")
        st.write(f"题目: {res['试题']}")
        st.write(f"标准答案: {res['标准答案']}")
        st.write(f"答题人数: {res['答题人数']}")
        st.write(f"正确率: {res['正确率']:.2f}%")

        if not res['错误答案统计'].empty:
            st.write("#### 错误答案统计")
            error_stats = res['错误答案统计']
            bar_chart = alt.Chart(error_stats).mark_bar(color='red').encode(
                y=alt.Y('答案', sort='-x'),
                x='出现次数',
                tooltip=['答案', '出现次数', '学生']
            )
            st.altair_chart(bar_chart, use_container_width=True)
            
            for _, row in error_stats.iterrows():
                color = 'green' if row['答案'] == res['标准答案'] else 'red'
                st.markdown(f"<div style='color:black;'>答案: <span style='color:{color};'>{row['答案']}</span></div>", unsafe_allow_html=True)
                st.write(f"出现次数: {row['出现次数']}")
                st.write(f"学生: {row['学生']}")
                st.write("")
    
    st.success("统计完成！")
else:
    st.error("当前目录下没有找到任何xlsx文件。")
