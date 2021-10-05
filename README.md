###### tags: `Project`

# Chatroom Python 
[TOC]

[<font color=yellow>SOURCE CODE Here</font>](https://github.com/maxwolf621/Cnotz)

> Reference ：　
>- Tkinter GUI programming by example 
>- 特洛伊木馬病毒程式設計(加強版)
>- Foundations of Python Network Programming

## Brief

![](https://i.imgur.com/Uanu8P8.png)

A Simple project of a GUI chat room.
- The user can send/download file and do a public/private chat with 3 servers(Download, Chat and Upload Server).
- Each file will include md5 algorithm encryption before sending


## Demo

![](https://i.imgur.com/zgKw7V1.png)

## Development environment
OS : `Debian Version 10.4 , Raspberry Pi 4`


## Design Concept 

1. Thread   
![](https://i.imgur.com/oX0baiV.jpg)
2. File Transfer 
    - Each transferring file with headers
        - Each Header may contain some information 
            > (e.g. File Size, File Name, File Digest ..)
    - There are two methods to send a file
        - Send a file at one time    
            - ![](https://i.imgur.com/20Ycqpc.png)
        - Split file to parts(blocks) if file is too large
            - ![](https://i.imgur.com/kw0ZHsC.png)
4. GUI interface
    - tkinter
6. Transferring file will include md5 header
    - Using md5 to check if file have been tampered with
    ![](https://i.imgur.com/98eZgqs.png)


