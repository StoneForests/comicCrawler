#coding:utf-8


import io
import sys
import os
import requests
import threading 
from time import sleep, ctime 
import string 

import requests
from fake_useragent import UserAgent
from lxml import etree

from PIL import Image
import re
import collections

from multiprocessing import Queue
from Queue import Empty, Full

from threadUtil import threadLoop
########################		下载线程		#################
#输入：
#		#url:https://18h.animezilla.com/manga/3689
#		#page:1-lastPage
#		#dir_path:3689-xxxxxx [215P]
#输出:
#		#3689-xxxxxx [215P]/1.jpg
#		#3689-xxxxxx [215P]/2.jpg
#		#...
#		#3689-xxxxxx [215P]/lastPage.jpg
class PageDownloadThread(threading.Thread):
	def __init__(self, args):
		self.url = args[0]
		self.dir_path = args[1]
		self.page = args[2]
		self.queue =args[3]
		threading.Thread.__init__(self)
		
	def animezilla(self):
		#web_url = 'https://18h.animezilla.com/manga/3689/2'
		#img_url = 'https://m.iprox.xyz/s/20190114/004668f1.jpg'
		web_url = self.url
		
		if self.page != 1 :
			web_url = '%s/%d' % (self.url,self.page)
		
		#判断文件存在
		img_filename = '%s\\%d.jpg'%(self.dir_path,self.page)
		if not os.path.exists(img_filename):
			#获取并解析页面
			web_data = requests.get(web_url).content.decode('utf-8')
			html = etree.HTML(web_data)
			img_url = html.xpath("//div[@id='page-current']//img/@src")
			if img_url:
				img_url = img_url[0]
			else:
				#最后一页regex变了
				img_url = html.xpath("//div[@class='entry-content']//img/@src")[0]
			#模拟浏览器
			ua = UserAgent()
			headers = {'User-Agent':ua.random,'Referer':web_url}
			response = requests.get(img_url,headers=headers)
			#图片保存
			img_file = Image.open(io.BytesIO(response.content))
			img_file.save(img_filename)
			self.queue.put('%s done!\n'%img_filename)
			print('%s done!\n'%img_filename)
		else:
			self.queue.put('%s exists\n'%img_filename)
	def run(self):
		self.animezilla()

########################		任务调度线程		#################
#输入：
#		#
#		#
#		#
#输出:
#		#
#		#
#		#
#		#
class BookManageThread(threading.Thread):
	def __init__(self, args):
		self.url = args[0]
		self.queue = args[1]
		threading.Thread.__init__(self)
	def BookManage(self):
		PAGE_DOWNLOAD_THREAD_NUM = 3
		web_url = self.url
		
		#书ID!!!
		book_id_rindex = web_url.rfind('/')
		book_id = web_url[book_id_rindex+1:]
		#print('book_id :%s\n'%book_id)
		print('BookManage:resolve book:%s\n'%book_id)
		
		#获取页面资源
		web_url = '%s/2'%self.url
		web_data = requests.get(web_url).content.decode('utf-8')
		html = etree.HTML(web_data)
		web_url = self.url
		
		#书名!!!
		book_name = html.xpath("//h1[@class='entry-title']//a/text()")[0].encode('gbk','ignore')
		book_name_index = book_name.rfind('/')
		book_name = book_name[book_name_index+1:]
		#print('book_name:%s\n'%book_name)
		
		#创建文件夹!!!
		dir_path = '%s-%s'%(book_id,book_name)
		if not os.path.exists(dir_path):
			os.mkdir(dir_path)
			print('mkdir %s\n'%dir_path)
		
		#totalPage
		title = html.xpath("//h1[@class='entry-title']/text()")[0]
		print('%s\n'%title)
		rIndex = title.rfind('/')
		totalPage = title[rIndex+1:]
		totalPage = string.atoi(totalPage)
		print('%s has %d pages!\n'%(dir_path,totalPage))
		print('Download begin...\n')
		
		threads = []
		end_page_cnt = 0
		thread_queue = Queue(maxsize=1000)
		if(totalPage > 1):
			for i in range(1,totalPage+1) :
				img_filename = '%s\\%d.jpg'%(dir_path,i)
				if not os.path.exists(img_filename):
					threadLoop(threads, PageDownloadThread, (web_url,dir_path,i,thread_queue), PAGE_DOWNLOAD_THREAD_NUM)
					print('start downloading %s ...\n'%img_filename)
				else:
					end_page_cnt = end_page_cnt + 1
					print('%s exists\n'%img_filename)
			while True:
				try:
					queue_content = thread_queue.get(block=False)
					if queue_content :
						end_page_cnt = end_page_cnt + 1
					if end_page_cnt == totalPage:
						break
				except Empty:
					if end_page_cnt == totalPage:
						break
				sleep (1)
			print('end_page_cnt:%d\n'%end_page_cnt)
		self.queue.put('%s-%s done'%(book_id,book_name))
		'''
		wflag = True
		while wflag:
			if len(threads) < PAGE_DOWNLOAD_THREAD_NUM:
				t = PageDownloadThread((web_url, dir_path, i))
				t.setDaemon(True)
				t.start()
				threads.append(t)
				wflag = False
			for th in threads:
				if not th.isAlive():
					threads.remove(th)
				if wflag == True:
					sleep(1)
		'''

	def run(self):
		self.BookManage()
########################		搜索线程		#################
#输入：
#		#
#		#
#		#
#输出:
#		#
#		#
#		#
#		#
#规则
#持久层
def search(url, list_book, dict_search):
	regex_search = 	['(18h.animezilla.com/topic$)',\
					 '(18h.animezilla.com/doujinshi$)',\
					 '(18h.animezilla.com/doujinshi/page/\d+$)',\
					 '(18h.animezilla.com/manga$)',\
					 '(18h.animezilla.com/manga/page/\d+$)',\
					 '(18h.animezilla.com/doujinshi/original$)',\
					 '(18h.animezilla.com/doujinshi/original/page/\d+$)',\
					 '(18h.animezilla.com/doujinshi/parody$)',\
					 '(18h.animezilla.com/doujinshi/parody/page/\d+$)']
	regex_book = 	['(18h.animezilla.com/manga/\d+)']

	web_url = url
	
	#书ID!!!
	book_id_rindex = web_url.rfind('/')
	book_id = web_url[book_id_rindex+1:]
	#print('book_id :%s\n'%book_id)

	#获取页面资源
	web_data = requests.get(web_url).content.decode('utf-8')
	html = etree.HTML(web_data)
	
	#书链接名!!!
	book_links = html.xpath("//a/@href")
	book_link_num = 0
	for bl in book_links:
		for r in regex_search:
			if re.findall(r,bl):
				bl_index = bl.find('18h.animezilla.com')
				bl = 'https://%s'%bl[bl_index:]
				if not dict_search[bl]:
					dict_search[bl] = 'F'
					book_link_num=1+book_link_num
					print('link:%s'%bl)
				#print bl
		'''
		for r in regex_book:
			if re.findall(r,bl):
				print bl
		'''
	print('%s add %d links\n'%(web_url,book_link_num))
	print('-----')

def init(dict_search):
	sflag = True
	while(sflag):
		sflag = False
		for k,v in dict_search.items():
			if v == 'F':				
				sflag = True
				dict_search[k] = 'T'
				search(k,list_book,dict_search)
	
	for k in sorted(dict_search):
		dict_search[k] = 'F'
		print k

if __name__ == '__main__':
	url = 'https://18h.animezilla.com/'
	
	url2 = 'https://18h.animezilla.com/doujinshi/page/2'
	url3 = 'https://18h.animezilla.com/doujinshi/page/3'
	url4 = 'https://18h.animezilla.com/doujinshi/page/4'
	url5 = 'https://18h.animezilla.com/doujinshi/page/5'
	url6 = 'https://18h.animezilla.com/doujinshi/page/6'
	url7 = 'https://18h.animezilla.com/doujinshi/page/7'
	
	list_book = [	'https://18h.animezilla.com/manga/3783',\
					'https://18h.animezilla.com/manga/3775',\
					'https://18h.animezilla.com/manga/3777',\
					'https://18h.animezilla.com/manga/3773',\
					'https://18h.animezilla.com/manga/3766',\
					'https://18h.animezilla.com/manga/3757']
	dict_search = collections.defaultdict(list)
	dict_search[url] = 'F'
	
	dict_search[url2] = 'F'
	dict_search[url3] = 'F'
	dict_search[url4] = 'F'
	dict_search[url5] = 'F'
	dict_search[url6] = 'F'
	dict_search[url7] = 'F'
	
	#init(dict_search)
	BOOK_MANAGE_THREAD_NUM = 3
	threads = []
	totalBook = len(list_book)
	end_booktask_cnt = 0
	thread_queue = Queue(maxsize=2*BOOK_MANAGE_THREAD_NUM)
	
	if(totalBook > 0):
		for i in range(totalBook) :
			threadLoop(threads, BookManageThread, (list_book[i],thread_queue), BOOK_MANAGE_THREAD_NUM)		
	while True:
		try:
			queue_content = thread_queue.get(block=False)
			if queue_content :
				end_booktask_cnt = end_booktask_cnt + 1
			if end_booktask_cnt == totalBook:
				break
		except Empty:
			if end_booktask_cnt == totalBook:
				break
		sleep (1)
	
	#BookManage(url)	
	
	'''
	files_dirs = os.listdir('.')
	dirlist = []
	for d in files_dirs:
		d_index = d.find('-')
		if d_index != -1:
			dirlist.append(d[:d_index])
	for d in dirlist:
		print('%s\n'%d)
	'''
	
'''
[	'https://18h.animezilla.com/', \
	'https://18h.animezilla.com/doujinshi', \
	'https://18h.animezilla.com/doujinshi/original', \
	'https://18h.animezilla.com/doujinshi/page/2', \
	'https://18h.animezilla.com/doujinshi/page/3', \
	'https://18h.animezilla.com/doujinshi/page/4', \
	'https://18h.animezilla.com/doujinshi/page/5', \
	'https://18h.animezilla.com/doujinshi/page/6', \
	'https://18h.animezilla.com/doujinshi/page/7', \
	'https://18h.animezilla.com/doujinshi/parody', \
	'https://18h.animezilla.com/doujinshi/parody/page/2', \
	'https://18h.animezilla.com/doujinshi/parody/page/3', \
	'https://18h.animezilla.com/doujinshi/parody/page/4', \
	'https://18h.animezilla.com/doujinshi/parody/page/5', \
	'https://18h.animezilla.com/doujinshi/parody/page/6', \
	'https://18h.animezilla.com/doujinshi/parody/page/7', \
	'https://18h.animezilla.com/manga', \
	'https://18h.animezilla.com/manga/page/10', \
	'https://18h.animezilla.com/manga/page/11', \
	'https://18h.animezilla.com/manga/page/12', \
	'https://18h.animezilla.com/manga/page/13', \
	'https://18h.animezilla.com/manga/page/14', \
	'https://18h.animezilla.com/manga/page/15', \
	'https://18h.animezilla.com/manga/page/16', \
	'https://18h.animezilla.com/manga/page/17', \
	'https://18h.animezilla.com/manga/page/18', \
	'https://18h.animezilla.com/manga/page/2', \
	'https://18h.animezilla.com/manga/page/3', \
	'https://18h.animezilla.com/manga/page/4', \
	'https://18h.animezilla.com/manga/page/5', \
	'https://18h.animezilla.com/manga/page/6', \
	'https://18h.animezilla.com/manga/page/7', \
	'https://18h.animezilla.com/manga/page/8', \
	'https://18h.animezilla.com/manga/page/9']
'''