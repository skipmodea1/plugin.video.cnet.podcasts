#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import StorageServer
import os
import re
import urllib
import urllib2
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmc
import sys
from bs4 import BeautifulSoup
from urlparse import parse_qs

ADDON = "plugin.video.cnet.podcasts"
SETTINGS = xbmcaddon.Addon(id=ADDON)
LANGUAGE = SETTINGS.getLocalizedString
IMAGES_PATH = os.path.join(xbmcaddon.Addon(id=ADDON).getAddonInfo('path'), 'resources', 'images')
CACHE = StorageServer.StorageServer("cnetpodcasts", 6)
LATEST_VIDEOS_HREF = 'http://feeds2.feedburner.com/cnet/allhdpodcast'
DATE = "2017-07-12"
VERSION = "1.0.4"


def make_request(url, post_data=None):
    headers = {
        'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0',
        'Referer': 'http://www.cnet.com'
    }
    try:
        req = urllib2.Request(url, post_data, headers)
        response = urllib2.urlopen(req)
        data = response.read()
        response.close()
        return data
    except urllib2.URLError, e:
        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
            ADDON, VERSION, DATE, "HTTPError", str(e)), xbmc.LOGDEBUG)
        xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30106) % (str(e)))
        exit(1)

def cache_categories():
    url = 'http://www.cnet.com/cnet-podcasts/'
    soup = BeautifulSoup(make_request(url), 'html.parser')
    items = soup.find_all('a', attrs={'href': re.compile("hd.xml$")})
    cats = [{'thumb': '',
             'name': i['href'],
             'desc': '',
             'links': i['href']} for
            i in items]
    return cats


def display_categories():
    cats = CACHE.cacheFunction(cache_categories)
    previous_name = ''

    # add a category
    name = 'Latest Videos'
    add_dir(name, LATEST_VIDEOS_HREF, 'category', '', {'Plot': ''})

    for i in cats:

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
            ADDON, VERSION, DATE, "cat", str(i)), xbmc.LOGDEBUG)

        name = str(i['name'])
        name = name.replace("http://feed.cnet.com/feed/podcast/", "")
        name = name.replace("-", " ")
        name = name.replace("/", " ")
        name = name.replace("hd.xml", "")
        name = name.capitalize()

        # skip name if it is the same as the previous name
        if name == previous_name:
            pass
        else:
            previous_name = name
            add_dir(name, i['links'], 'category', i['thumb'], {'Plot': i['desc']})


def display_category(links_list):
    url = links_list

    soup = BeautifulSoup(make_request(url), 'html.parser')

    # latest videos isn't a real category in CNET, therefore this hardcoded stuff was needed
    if url == LATEST_VIDEOS_HREF:
        urls = soup.find_all('a', attrs={'href': re.compile("^http://feedproxy.google.com/")})
        # <a href="http://feedproxy.google.com/~r/cnet/allhdpodcast/~3/4RHUa95GiUM/14n041814_walkingpalua_740.mp4">A walk among hidden graves and WWII bombs</a>
        for url in urls:
            title = str(url)
            title = title.replace('</a>', '')
            title = title.replace("&#039;", "'")
            pos_last_greater_than_sign = title.rfind('>')
            title = title[pos_last_greater_than_sign + 1:]

            meta = {'Plot': title,
                    'Duration': '',
                    'Date': '',
                    'Premiered': ''}

            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "url", str(url)), xbmc.LOGDEBUG)

            add_dir(title, url['href'], 'resolve', 'Defaultvideo.png', meta, False)
    else:
        #     <item>
        #           <title><![CDATA[Inside Scoop: Will acquiring Nokia devices give Microsoft an edge?]]></title>
        #           <link>http://www.podtrac.com/pts/redirect.mp4/dw.cbsi.com/redir/13n0903_MicrosoftScoop_740.m4v?destUrl=http://download.cnettv.com.edgesuite.net/21923/2013/09/03/13n0903_MicrosoftScoop_740.m4v</link>
        #           <author>feedback-cnettv@cnet.com (CNETTV)</author>
        #           <description><![CDATA[Details of the Microsoft and Nokia deal are now finalized. CNET's Josh Lowensohn discusses the effects the merger could have on customers, Microsoft's sagging market share, and the selection of a new Microsoft CEO.]]></description>
        #           <itunes:subtitle><![CDATA[Details of the Microsoft and Nokia deal are now finalized. CNET's Josh Lowensohn discusses the effects the merger could have on customers, Microsoft's sagging market share, and the selection of a new Microsoft CEO.]]></itunes:subtitle>
        #           <itunes:summary><![CDATA[Details of the Microsoft and Nokia deal are now finalized. CNET's Josh Lowensohn discusses the effects the merger could have on customers, Microsoft's sagging market share, and the selection of a new Microsoft CEO.]]></itunes:summary>
        #           <itunes:explicit>no</itunes:explicit>
        #           <itunes:author>CNET.com</itunes:author>
        #           <guid isPermaLink="false">35ffbba2-67e4-11e3-a665-14feb5ca9861</guid>
        #           <itunes:duration></itunes:duration>
        #           <itunes:keywords>
        #               CNET
        #                CNETTV
        #             Tech Industry
        #           </itunes:keywords>
        #           <enclosure url="http://www.podtrac.com/pts/redirect.mp4/dw.cbsi.com/redir/13n0903_MicrosoftScoop_740.m4v?destUrl=http://download.cnettv.com.edgesuite.net/21923/2013/09/03/13n0903_MicrosoftScoop_740.m4v" length="0" type="video/mp4"/>
        #           <category>Technology</category>
        #           <pubDate>Fri, 21 Feb 2014 19:49:08 PST</pubDate>
        #     </item>
        urls = soup.find_all('enclosure', attrs={'url': re.compile("^http")})

        # skip 2 titles
        title_index = 2

        for url in urls:
            titles = soup.find_all('title')
            title = str(titles[title_index])
            title_index = title_index + 1
            title = title.replace("<title><![CDATA[", "")
            title = title.replace("]]></title>", "")
            title = title.replace("&#039;", "'")

            meta = {'plot': title,
                    'duration': '',
                    'year': '',
                    'dateadded': ''}

            add_dir(title, url['url'], 'resolve', 'Defaultvideo.png', meta, False)


def add_dir(name, url, modus, iconimage, meta=None, isfolder=True):
    add_sort_methods()

    context_menu_items = []
    # Add refresh option to context menu
    context_menu_items.append((LANGUAGE(30104), 'Container.Refresh'))
    # Add episode  info to context menu
    context_menu_items.append((LANGUAGE(30105), 'XBMC.Action(Info)'))

    if meta is None:
        meta = {}
    parameters = {'name': name, 'url': url, 'mode': modus}
    url = '%s?%s' % (sys.argv[0], urllib.urlencode(parameters))
    list_item = xbmcgui.ListItem(name, thumbnailImage=iconimage)
    if isfolder:
        list_item.setProperty('IsPlayable', 'false')
    else:
        list_item.setProperty('IsPlayable', 'true')
    list_item.setProperty('Fanart_Image', os.path.join(IMAGES_PATH, 'fanart-blur.jpg'))
    list_item.setInfo("mediatype", "video")
    list_item.setInfo("video", meta)
    # Adding context menu items to context menu
    list_item.addContextMenuItems(context_menu_items, replaceItems=False)
    # Add our item to directory
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, list_item, isfolder)


def add_sort_methods():
    sort_methods = [xbmcplugin.SORT_METHOD_UNSORTED,xbmcplugin.SORT_METHOD_LABEL,xbmcplugin.SORT_METHOD_DATE,xbmcplugin.SORT_METHOD_DURATION,xbmcplugin.SORT_METHOD_EPISODE]
    for method in sort_methods:
        xbmcplugin.addSortMethod(int(sys.argv[1]), sortMethod=method)


def get_params():
    p = parse_qs(sys.argv[2][1:])
    for i in p.keys():
        p[i] = p[i][0]
    return p


def set_view_mode():
    view_modes = {
        '0': '502',
        '1': '51',
        '2': '3',
        '3': '504',
        '4': '503',
        '5': '515'
    }
    view_mode = SETTINGS.getSetting('view_mode')
    if view_mode == '6':
        return
    xbmc.executebuiltin('Container.SetViewMode(%s)' % view_modes[view_mode])

params = get_params()

try:
    mode = params['mode']
except:
    mode = None
    xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s, %s = %s" % (
        ADDON, VERSION, DATE, "ARGV", repr(sys.argv), "File", str(__file__)), xbmc.LOGDEBUG)

xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
    ADDON, VERSION, DATE, "params", str(params)), xbmc.LOGDEBUG)

if not mode:
    display_categories()
    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'category':
    display_category(params['url'])
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    set_view_mode()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'resolve':
    item = xbmcgui.ListItem(path=params['url'])
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
