#!/usr/bin/env python
# coding: utf-8

# 根据文本来剪辑视频
# 
# 程序依赖
# 
# * srt https://github.com/cdown/srt
# * webvtt-py https://github.com/glut23/webvtt-py
# 
# 来处理字幕

# In[ ]:


import srt # https://github.com/cdown/srt
import webvtt # https://github.com/glut23/webvtt-py
import os
import pandas as pd
import difflib
import subprocess
import argparse
from tempfile import TemporaryDirectory

from sub2txt import sub_to_df, df_to_txt,get_sub_files


# 如果没有编辑txt文本来生成摘要，那么就没有必要去对视频进行剪辑，否则按照现在的做法会把整个视频切分成一句一句再合并起来。
# 所以需要判断一个评分，看看字幕文件和txt文本之间是否有足够的内容差别。
# 
# difflib.SequenceMatcher(None, text1, text2).quick_ratio()可以快速生成两个文本之间相似程度的评分，如果高于阈值，就不必进行后续剪辑的处理了

# In[ ]:


def summary_score(df, txt):
    '''
    比较字幕文件和summary文件是否有差异，如果差异太小，后续则不做视频剪辑处理
    '''
    df_txt=df_to_txt(df)
    s=difflib.SequenceMatcher(None, df_txt, txt) 
    return(s.quick_ratio())


# 在路径中找到与输入文件名最接近的文件名
# 
# difflib.SequenceMatcher(None, text1, text2).ratio()可以快速生成两个文本之间相似程度的评分，用这个来找到目录中最相似的文件名。因为字幕文件往往会带有语言标记，比如.zh-CN.srt之类，懒得去一步一步判断了，直接用评分来比较好了。

# In[ ]:


def get_most_simliar_filename(target_filename, path, ext):
    '''
    在路径中找到与输入文件名最接近的文件名
    '''
    candidate=get_sub_files(path,[],ext)
    simliar_score=[difflib.SequenceMatcher(None,c,target_filename).ratio() for c in candidate]
    max_index=simliar_score.index(max(simliar_score))
    return(candidate[max_index])


# 在字幕df中，一句一句寻找text中的内容，将最接近的挑出来

# In[ ]:


def find_text_in_df(text,df):
    '''
    '''
    chosen_text=[]
    for t in text.splitlines():
        sentence=difflib.get_close_matches(t,df["text"],n=1)
        if sentence:
            chosen_text.extend(sentence)
    df_chosen=pd.DataFrame(chosen_text,columns=["text"])
    df_chosen=df_chosen.merge(df)
    return df_chosen


# 重建字幕
# 
# 挑出来的字幕数据，想重建成一个新的字幕文件，但是挑选出来的字幕数据，时间戳是原来的时间，需要合并到一起，那么先计算每一句话花了多少时间，再累积起来。

# In[ ]:


def rebuild_sub(df_chosen,output_filename):
    df_chosen["delta_time"]=pd.to_datetime(df_chosen["end"])-pd.to_datetime(df_chosen["start"])
    df_chosen["new_end"]=df_chosen["delta_time"].cumsum()
    df_chosen["new_start"]=df_chosen["new_end"]-df_chosen["delta_time"]
    new_sub_df=df_chosen[["new_start","new_end","text"]]

    subs=[srt.Subtitle(index=i,
                 start=new_sub_df.new_start[i], 
                 end= new_sub_df.new_end[i], 
                 content=new_sub_df.text[i])
          for i in range(len(new_sub_df))]
    srt_content=srt.compose(subs)
    # 写入output_filename的同名srt文件
    base_name,ext=os.path.splitext(output_filename)
    srt_file_name=base_name+".srt"
    with open(srt_file_name,"w") as f:
        f.write(srt_content)


# 利用ffmpeg来根据起止时间剪辑视频。

# In[ ]:


def clip_video(video_filename, start, end,output_filename):
    ffmpeg_command=['ffmpeg',
         '-ss',start,
         '-i',
         video_filename,
         '-to', end,
         '-c:v', 'libx264', '-c:a', 'libmp3lame', #视频重编码使用x264, 音频重编码使用mp3
         '-copyts', # 强制使用原视频的绝对时间
         '-y', # 强制覆盖
         output_filename]
    p=subprocess.run(ffmpeg_command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return(p.stdout.decode("utf-8"))


# In[ ]:





# In[ ]:


def clip_video_by_keynote(df, video_filename, final_output):
    # 产生临时目录，with完成后自动销毁
    with TemporaryDirectory() as temp_path:
        #临时文件命名, 记录临时文件列表
        temp_file_list=[os.path.join(temp_path,"tmp_{}.mp4".format(index)) for index in range(len(df))]
        temp_input=os.path.join(temp_path,'tmp_input_files.txt')
        with open(temp_input,'w') as f:
            for index in range(len(df)):
                f.write("file '{}'\n".format(temp_file_list[index]))    
    
        # 遍历数据库, 下载每个视频片段
        for index, row in df.iterrows():
            clip_video(video_filename, row.start, row.end,temp_file_list[index])

        # 将临时文件合并起来
        ff_concat_command=["ffmpeg", 
                       '-f','concat',
                       '-safe','0',
                       '-i', temp_input,
                       '-c:v', 'copy', '-c:a', 'copy', '-copyts', #合并似乎不需要重新编码
                       '-y',
                       final_output # final_output的路径并不在temp目录下，所以不会被销毁
                       ]
        ff=subprocess.run(ff_concat_command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return ff


# In[ ]:


def clip_one(txt_file, srt_file, video_file, output_file, threshold=0.8):
    print("{}".format(os.path.basename(video_file)))
    with open(txt_file,"r") as f:
        txt=f.read()
    df_ori=sub_to_df(srt_file)
    
    if summary_score(df_ori,txt)> threshold: # 太接近，没必要进行剪辑了。
        print("...Pass ")
        return 
    df_chosen=find_text_in_df(txt,df_ori)
    clip_video_by_keynote(df_chosen, video_file, output_file)
    rebuild_sub(df_chosen,output_file)
    print("...Done ")


# In[ ]:


def clip_path(path):
    # 找到path下所有的txt文件
    txt_file_list=get_sub_files(path,[],"txt")
    # 找到path下与txt文件名最接近的字幕文件
    sub_file_list=[get_most_simliar_filename(t, path, ("srt","vtt")) for t in txt_file_list]
    # 找到path下与txt文件名最接近的视频文件
    video_file_list=[get_most_simliar_filename(t, path, ("mp4","mov")) for t in txt_file_list]
    
    for t,s,v in zip(txt_file_list,sub_file_list,video_file_list):
        o=os.path.join(os.path.dirname(v),"summary_"+os.path.basename(v))
        clip_one(t, s, v, o, threshold=0.8)


# 定义命令行参数, 必要时可以指定这些文件，否则默认为输入的是txt文件或者是路径。
# * -s 字幕文件
# * -v 视频文件
# * -o 输出文件
# 
# 如果输入的是目录路径，则遍历其下所有txt文件。

# In[ ]:


def arg_parse():
    '''
    解析命令行参数
    '''
    # 创建解析步骤
    parser = argparse.ArgumentParser(description='Clip video based on txt summary file.')

    # 添加参数步骤
    parser.add_argument("input", type=str,
                       help="a txt file or a path.")
    
    
#     parser.add_argument('-t','--txt',  type=str, 
#                        help='txt file, the summary')
#     parser.add_argument('-p','--path',  type=str, 
#                        help='path')
    
    
    parser.add_argument('-s','--sub',  type=str, 
                       help='subtitle file')    
    parser.add_argument('-v','--video',  type=str, 
                       help='video file')
    parser.add_argument('-o','--output',  type=str, 
                       help='output video file')


    # 解析参数步骤  
    args = parser.parse_args()
    return(args)


# In[ ]:


if __name__=="__main__":
    args=arg_parse()
    sub_format=("srt","vtt")
    video_format=("mp4","mov","mkv")
    
    if os.path.isfile(args.input): # 处理单个文件
        
        path=os.path.dirname(args.input)
        if path=="": # 如果是本地目录
            path=os.path.abspath(os.path.dirname(__file__))
        if args.sub==None:
            args.sub=get_most_simliar_filename(args.input, path, sub_format)
        if args.video==None:
            args.video=get_most_simliar_filename(args.input, path, video_format)
        if args.output==None:
            v=args.video
            args.output=os.path.join(os.path.dirname(v),"summary_"+os.path.basename(v))
        
        clip_one(args.input, args.sub, args.video, args.output,threshold=0.8)
        
    elif os.path.isdir(args.input): # 处理目录下所有txt文件
        clip_path(args.input)
    


# In[ ]:





# In[ ]:




