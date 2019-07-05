#!/usr/bin/env python
# coding: utf-8

# 将字幕转换为txt文件，支持vtt文件或者srt文件。

# In[2]:


import srt
import webvtt
import os
import pandas as pd
import subprocess
import argparse


# 读取vtt文件到pandas DataFrame

# In[ ]:


def vtt_to_df(vtt_filename):
    vtt=webvtt.read(vtt_filename)
    lines = []
    starts = []
    ends = []
    for line in vtt:
        extend_text=line.text.strip().splitlines()
        repeat=len(extend_text)
        lines.extend(extend_text)
        starts.extend([line.start] * repeat)
        ends.extend([line.end] * repeat)

    previous = None
    new_lines=[]
    new_starts=[]
    new_ends=[]

    for l,s,e in zip(lines,starts,ends):
        if l == previous:
            continue
        else:
            new_lines.append(l)
            new_starts.append(s)
            new_ends.append(e)
            previous = l

    df={"start":new_starts,"end":new_ends,"text":new_lines}
    df=pd.DataFrame(df)
    return df
    


# 读取srt文件，到pandas dataframe

# In[37]:


def srt_to_df(srt_filename):
    with open(srt_filename) as f:
        srt_content=f.read()
#         srt_content=srt.make_legal_content(srt_content)
    df=pd.DataFrame([[str(s.start).split(" ")[-1],
                      str(s.end).split(" ")[-1],
                      s.content] for s in srt.parse(srt_content)])
    df.columns=["start","end","text"]
    return df


# 读入的文件可能是两者之一

# In[ ]:


def sub_to_df(input_filename):
    base_name,ext=os.path.splitext(input_filename)
    if ext.lower()==".vtt":
        df=vtt_to_df(input_filename)
    elif ext.lower()==".srt":
        df=srt_to_df(input_filename)
    else:
        print(ext)
        raise Exception("not a subtitle file") 
    return df


# 将pandas dataframe转换为纯文本

# In[38]:


def df_to_txt(df):
    transcript="\n".join(df["text"])
    return transcript 


# 将文本写入到文件中

# In[ ]:


def write_to_txt(output_filename, text):
    with open(output_filename,"w") as f:
        f.write(text)


# 对于未曾定义输出文件名的，将后缀改为txt作为输出文件名

# In[ ]:


def repeat_input_to_output_filename(input_filename):
    base_name,ext=os.path.splitext(input_filename)
    return(base_name+".txt")


# 处理每一个单独文件

# In[ ]:


def one_sub_to_txt(input_filename, output_filename):
    df=sub_to_df(input_filename)
    text=df_to_txt(df)
    write_to_txt(output_filename, text)


# 遍历目录下所有扩展名在```ext=("vtt","srt")```内的文件，返回所有文件名

# In[32]:


def get_sub_files(rootDir,file_list,ext): 
    for lists in os.listdir(rootDir): 
        name = os.path.join(rootDir, lists)  
        if os.path.isdir(name): 
            get_sub_files(name,file_list,ext)
        elif os.path.isfile(name):
            if name.endswith(ext):
                file_list.append(name)
    return file_list


# argparse是一种好用的定义命令行参数的工具，本次定义如下：
# * -p 输入路径，遍历路径下所有字幕文件，将其转换为txt，若-p存在，则-i，-o无效
# * -i 输入单一文件名，将其转换为txt
# * -o 在-p存在时无效，对于单一文件，-o指定了输出txt文件名

# In[ ]:


def arg_parse():
    '''
    解析命令行参数
    '''
    # 创建解析步骤
    parser = argparse.ArgumentParser(description='Process TTS')

    # 添加参数步骤
    parser.add_argument('-i','--input',  type=str, 
                       help='subtitle file, the filetype should be vtt or srt')
    parser.add_argument('-p','--path',  type=str, 
                       help='path')
    parser.add_argument('-o','--output',  type=str, 
                       help='output filename.')

    # 解析参数步骤  
    args = parser.parse_args()
    return(args)


# In[ ]:


if __name__=="__main__":
    # 解析命令行参数
    args=arg_parse()
    if args.path:
        file_list=get_sub_files(args.path,[],("vtt","srt"))
        for input_filename in file_list:
            output_filename=repeat_input_to_output_filename(input_filename)
            one_sub_to_txt(input_filename, output_filename)
    elif args.input:
        if args.output:
            one_sub_to_txt(args.input, args.output)
        else:
            output_filename=repeat_input_to_output_filename(args.input)
            one_sub_to_txt(args.input, output_filename)
            

