from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import copy
import urllib.parse
import re
import requests
from settings import settings


ipam_username=settings.get('ipam_username')
ipam_password=settings.get('ipam_password')
ipam_host=settings.get('ipam_host')
root_zone_id=settings.get('root_zone_id')

chrome_options = Options()
#chrome_options.add_argument("--headless")
driver = webdriver.Chrome(options=chrome_options)

driver.get("https://"+ipam_host)
driver.find_element_by_id("username").send_keys(ipam_username)
driver.find_element_by_id("password").send_keys(ipam_password)
driver.find_element_by_id("loginButton").click()

#steal session cookie to use with requests library
cookie_jar = requests.cookies.RequestsCookieJar()
cookie_jar.set('JSESSIONID', driver.get_cookie('JSESSIONID')['value'], domain=ipam_host, path='/')


# had to do it this way to get it to urlencode properly as a query string
zones_list_params=[
    ('component', '$TabbedEntityContainer.contextContainer.contextTabLink'),
    ('session', 'T'),
    ('page', 'ZoneDetails'),
    ('service', 'direct'),
    ('sp','Spage=ZoneDetails'),
    ('sp','ScontextId=subZones')
]


# export query params, excluding zone id
export_query_params={
  'component': ['$Border'],
  'session': ['T'],
  'sp': ['SworkflowMode=false',
         'SexportTablePageSize=10000',
         'ScontextId=records',
         'SexportEnabled=true',
         'StableUseDetailPaneFields=true',
         'SexportType=MODEL_TABLE',
         'SrenderSubRegionOnly=true',
         'Spage=ZoneDetails',
         'SsubRegionId=ValueObjectFormTableRegionResourceRecord',
         'SexportTablePageNumber=2147483647',
         'SexportTableColumns=$$name|$$type|$$recordData|$$dynamic|',
         'SexportFormat=CSV',
         'SexportTableStartRow=1',
         'SexportFileName=Resource Records',
         'X'],
  'page': ['ExportHandlerPage'],
  'service': ['direct']
}


# get subzone list
params = zones_list_params
params.append(('sp','Svalue=Zone:'+root_zone_id))
driver.get("https://"+ipam_host+"/app?"+urllib.parse.urlencode(params))

# this is kinda gross, but it worked..
subzones=driver.find_elements_by_xpath('//table[@id="outerTable"]/tbody/tr[*]//table//tr/td[2]/a')


# export root zone
params = copy.deepcopy(export_query_params)
params["sp"].append('Svalue=Zone:'+root_zone_id)
resp = requests.get("https://"+ipam_host+"/app", params=params, cookies=cookie_jar)
with open("./zones/root_zone.csv", "wb") as f:
    f.write(resp.content)

# export subzones
for zone in subzones:
    subzone_id_param=urllib.parse.parse_qs(zone.get_property("href"))['sp'][0]
    params = copy.deepcopy(export_query_params)
    params["sp"].append(subzone_id_param)
    print("downloading: "+zone.text + "   with zone_id: " + subzone_id_param)
    resp = requests.get("https://" + ipam_host + "/app", params=params, cookies=cookie_jar)

    with open("./zones/"+zone.text+".csv", "wb") as f:
        f.write(resp.content)
driver.quit()  # don't need this anymore
