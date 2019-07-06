# Video Keynotes
根据重点笔记对视频课程进行剪辑，方便划重点复习。

# 使用
* 需先下载课程视频和字幕文件
    * coursera上的课程可以使用[coursera-dl](https://github.com/coursera-dl/coursera-dl)进行下载。注意其中的[china-issues](https://github.com/coursera-dl/coursera-dl#china-issues), 可能需要通过VPN才能正常访问国际互联网。
        * 使用coursera-dl下载出现"HTTPError:400"问题，请参考[此解决方案](https://github.com/coursera-dl/coursera-dl/issues/702#issuecomment-506929946)
    * Youtube上的课程，例如OCW，可以使用[youtube-dl](https://rg3.github.io/youtube-dl/)进行下载。注意需要将对应的字幕也下载下来
* 将字幕文件处理成txt脚本
    * 处理单个文件：``` python sub2txt.py <subtitle file name>```
    * 处理整个目录：``` python sub2txt.py <path>```
* 手动编辑txt脚本，将你认为不重要的部分删除后保存，尽量不要修改txt文件名
* 按编辑后的txt脚本剪辑视频课程：
    * 处理单个文件：```python clip_by_txt.py <txt file>```
    * 处理整个目录：```python clip_by_txt.py <path>```

剪辑完成的视频将以summary_开头，存储在视频课程原位，并且附带有srt的字幕。

# Demo

这是一个剪辑自coursera上的learning how to learn课程第一周第一课[introduction-to-the-focused-and-diffuse-modes](https://www.coursera.org/learn/learning-how-to-learn/lecture/75EsZ/introduction-to-the-focused-and-diffuse-modes) 

* [Youtube视频：](https://www.youtube.com/embed/UjkYY6HUSyY)

