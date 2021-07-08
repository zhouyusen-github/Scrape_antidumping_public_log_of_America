import json
import uuid

import scrapy
from lxml import etree
import re
import copy

import sys

sys.path.append('./')

from items import NoticeItem, RateItem

def load_country():
    file = open("resource/country.json", "r")
    data = json.load(file)
    country_dict = {}
    for i in data:
        country_dict[i['en'].lower()] = True
    return country_dict

Petitioner_setting_len = 14
HS_setting_len = 80

field_list_together_front = ["CaseID", "ITCNo", "DOCNo", "Year", "Month", "Date", "ProducerID", "Action"]
field_list_together_last = ["Exporter", "ExpAltNm", "Producer", "PdAltNm", "AD_CVD", "Product", "Country", "source", "fed_reg", "Notes"] + \
                           [string.replace("$", str(i + 1)) for i in range(Petitioner_setting_len) for string in ["Petitioner$", "Ptner$AltNm"]] + \
                           ["HS" + str(i + 1) for i in range(HS_setting_len)]
field_list_AD = field_list_together_front + ["CashDeposit", "DumpingMargin"] + field_list_together_last
field_list_CVD = field_list_together_front + ["SubsidyRate"] + field_list_together_last


def could_float(float_string):
    try:
        float(float_string)
        return True
    except ValueError:
        return False

def get_hs_list(response_html):
    hs_list_10 = re.findall(r'\d{4}\.\d{2}\.\d{4}', response_html)
    hs_list_10_format2 = re.findall(r'\d{4}\.\d{2}\.\d{2}\.\d{2}', response_html)
    hs_list_8 = re.findall(r'\d{4}\.\d{4}', response_html)
    hs_list = hs_list_10 + hs_list_10_format2 + hs_list_8
    return hs_list


def get_Petitioners(response_html):  # 投诉有倾销现象的人
    Petitioners = re.findall(r'The Petition.*?</h\d>[\s\S]*?<p.*?[\s\S]*?<p', response_html)
    if len(Petitioners) == 0:
        return []
    Petitioners = Petitioners[0].replace("\n", "")
    # Petitioners = re.sub(r'<sup>.*?</sup>', "", Petitioners)
    Petitioners = re.sub(r'<span.*</span>', "", Petitioners)
    Petitioners = re.sub(r'<p.*?>', "", Petitioners)
    Petitioners = re.sub(r'</p>.*?<p', "", Petitioners)
    Petitioners = re.sub(r'.*?</h\d>\s*?', "", Petitioners)
    Petitioners = Petitioners.replace("  ", " ")
    Petitioners = Petitioners.replace("Co.", "Company Limited")
    Petitioners = Petitioners.replace(", Inc.", " Incorporated")
    Petitioners = Petitioners.replace("Corp.", "Corporation")
    Petitioners = Petitioners.replace("Ltd.", "Company Limited")
    # 如果有冒号以冒号为分隔
    Petitioners = Petitioners.replace("U.S.", "US")
    answer = re.findall(r'proper form.*?\.', Petitioners)
    if len(answer) == 0:
        answer = re.findall(r':.*.', Petitioners)
    if len(answer) == 0:
        return []
    answer = answer[0]
    answer = re.sub(r'proper form.*?:', "", answer)  # 这个sub顺序是有原因的
    answer = re.sub(r'proper form.*?(parties)', "", answer)
    answer = re.sub(r'proper form.*?(for|of|by)', "", answer)
    answer = re.sub(r'\(.*?\)', "", answer)
    answer = re.sub(r'\(.*?\)', "", answer)
    answer = re.sub(r'\(.*?\)', "", answer)
    answer = re.sub(r'\(.*?\)', "", answer)
    answer = re.sub(r'and', "", answer)
    answer = answer.split(",")
    answer = [i.strip(".").strip(" ") for i in answer]
    # print(answer)
    return answer

# 1. DOC No. : Agency/Docket Number:
# 以外情况，可能有多个
def get_docket_number(html_tree):
    order = meta_list_get("Agency/Docket Number:", html_tree)
    docket_number_search = html_tree.xpath("//dl[@class='metadata_list']/dd[" + str(order) + "]/text()")
    if len(docket_number_search) > 0:
        docket_number = docket_number_search[0]
    else:
        docket_number = ""
    return docket_number

# 2. year_month_date:
# 这些字段的html的位置可能有变化所以这么操作
def meta_list_get(field_name: str, html_tree):
    metadata_list = html_tree.xpath("//dl[@class='metadata_list']/dt/text()")
    order = 0
    for i in metadata_list:
        order = order + 1
        if i == field_name:
            break
    return order


def get_year_month_date(html_tree):
    order = meta_list_get("Publication Date:", html_tree)
    docket_number = html_tree.xpath("//dl[@class='metadata_list']/dd[" + str(order) + "]/a/text()")[0]
    return docket_number


def fix_number_string(number_string):
    answer = number_string.replace("percent", "")
    answer = answer.strip()
    return answer


# 7. Company and Subsidy rate 都在表格哪里，解析成字典 进入数据库后 这里每个参数是一个单元
# 我想更改输出格式为  list list，每个dict是 producer，exporter，DumpingdumpingMargin，CashDeposit
def get_company_and_subsidy_rate_in_table(html_tree):
    theads = html_tree.xpath("//div[@class='table-wrapper']/table/thead")
    tbodys = html_tree.xpath("//div[@class='table-wrapper']/table/tbody")
    final_output_attributes = []
    # 判断是哪种类型的表格，并且规避无关表格
    for i in range(len(theads)):
        thead = theads[i]
        tbody = tbodys[i]
        row_attribute_relationship = {}  # 记录输出字段对应哪一列数据 比如第0列'Manufacturer/exporter' 意味这producer和exporter取表格第0行数据，dict的映射记录下来，解析时对应解析 ， 用has_key 判断是否有该字段
        # 把表格头提出来看看
        thead_th_texts = thead.xpath("./tr/th/text()")
        thead_th_trs = tbody.xpath("./tr")
        thead_th_texts_len = len(thead_th_texts)
        for i in range(thead_th_texts_len):  # 弄干净一点号分析
            thead_th_texts[i] = thead_th_texts[i].replace("\n", " ").replace("  ", "")
        # print(thead_th_texts)
        # 先判断列数，再判断意思

        # 解析表格
        # print(thead_th_texts_len)
        for m in range(thead_th_texts_len):
            title = thead_th_texts[m]
            title_lower = title.lower()
            if "producer" in title_lower or "manufacturer" in title_lower or "company" in title_lower:
                row_attribute_relationship['Producer'] = m
            if "exporter" in title_lower:
                row_attribute_relationship['Exporter'] = m
            if "margin" in title_lower:
                row_attribute_relationship['DumpingMargin'] = m
            if "deposit" in title_lower:
                row_attribute_relationship['CashDeposit'] = m
            if "subsidy" in title_lower:
                row_attribute_relationship['SubsidyRate'] = m
                # print("row_attribute_relationship['SubsidyRate']: "+str(row_attribute_relationship['SubsidyRate']))
            if "valorem" in title_lower:
                row_attribute_relationship['valorem'] = m
        if len(row_attribute_relationship) == 0:
            continue  # 说明可能解析到非数据的表格了

        sub_titles = tbody.xpath("./tr/td[@class='center border-bottom-single']/text()")
        if len(sub_titles) > 0:
            sub_title_low = sub_titles[0].lower()
            if "producer" in sub_title_low or "manufacturer" in sub_title_low or "company" in sub_title_low:
                row_attribute_relationship['Producer'] = 0
            if "exporter" in sub_title_low:
                row_attribute_relationship['Exporter'] = 0

        # 读取表内数据 返回类型 list dict
        # 空值取前值,取后值有两种情况
        Columns_front_memory = ["" for i in range(thead_th_texts_len)]  # 空值取前值用与缓存，因为有的公司和上一个公司费率相同，他就会空
        Columns_back_memory = []  # 空值取后值，把哪些列先缓存起来
        mode = 0  # 默认空值取前面
        rows = []
        for tr in thead_th_trs:  # 每一行数据
            tr_texts = tr.xpath("./td/text()")
            # tr_texts = tr.xpath("./td[@class!='center border-bottom-single']/text()")
            # print(tr_texts)
            if len(tr_texts) == 0:
                continue
            # 处理国家还是太麻烦了,如果所查询国家不在里面则
            # if len(tr_texts) == 1 and len(tr_texts) < thead_th_texts_len:
            #     pass
            # if "(and" in tr_texts[0]:
            #     continue
            if "following" in tr_texts[0].lower() and "compan" in tr_texts[0].lower():
                mode = 1
                continue
            if mode == 0:
                # print(0)
                Columns = ["" for i in range(thead_th_texts_len)]
                Columns[0] = tr_texts[0]
                if len(tr_texts) == thead_th_texts_len and len(tr_texts[thead_th_texts_len - 1].strip()) > 0:  # 本意是想如果是空格或者是空白，那么应该跳过
                    for title_index in range(1, thead_th_texts_len):
                        Columns_front_memory[title_index] = fix_number_string(tr_texts[title_index])
                for title_index in range(1, thead_th_texts_len):
                    Columns[title_index] = Columns_front_memory[title_index]
                rows.append(Columns)
            else:  # 2. 空值取后值
                # print(1)
                if len(tr_texts) == thead_th_texts_len and len(tr_texts[thead_th_texts_len - 1].strip()) > 0:
                    fix_tr_texts_list = [fix_number_string(tr_texts[title_index]) for title_index in range(1, thead_th_texts_len)]
                    for i in Columns_back_memory:
                        rows.append([i[0]] + fix_tr_texts_list)
                    rows.append([tr_texts[0]] + fix_tr_texts_list)
                    Columns_back_memory = []  # 缓存取出后，重新处理
                else:
                    Columns_back_memory.append(tr_texts)
        output_attributes = []
        for row in rows:
            output_raw_dict = {}
            # print(row)

            for k in ['Producer', 'Exporter', 'DumpingMargin', 'CashDeposit', 'SubsidyRate', 'valorem']:
                if k in row_attribute_relationship:
                    output_raw_dict[k] = row[row_attribute_relationship[k]].strip()[0:400]

            output_attributes.append(output_raw_dict)
            # print(output_raw_dict)
        # 解析出来的行数据 转换成 最终 四个要输出的数据
        final_output_attributes = final_output_attributes + output_attributes
    return final_output_attributes


# 8. Fed Reg: Document Citation
def get_fed_reg(html_tree):
    fed_reg = html_tree.xpath("//dd[@id='document-citation']/text()")[0].strip()
    return fed_reg


# 提取final result 段落
def get_final_result_chapter(response_html):
    # print("进入get_final_result_chapter")
    final_result_chapter = re.findall(r'>Final.*?Results.*?</h\d>[\s\S]*?</p>', response_html)
    if len(final_result_chapter) > 0:
        return final_result_chapter[0]
    else:
        return ""


def get_company_and_subsidy_rate_in_final_result_chapter(response_html):
    final_result_chapter_string = get_final_result_chapter(response_html)
    output_attributes = []

    output_raw_dict = {}
    DumpingMargin_list = re.findall(r'\d{1,4}\.\d{2}', final_result_chapter_string)
    if len(DumpingMargin_list) > 0:
        DumpingMargin = DumpingMargin_list[-1]  # 有的是更正，那么最后出现的那个率才是正确的
    else:
        DumpingMargin = ""
    Producer_list_string = re.search(r'by(.*?)during', final_result_chapter_string)
    if Producer_list_string != None:
        Producer = Producer_list_string.group(1)

    else:
        Producer = ""
    Exporter = Producer

    output_raw_dict['DumpingMargin'] = DumpingMargin
    output_raw_dict['Producer'] = Producer
    output_raw_dict['Exporter'] = Exporter
    output_raw_dict['CashDeposit'] = ""
    output_attributes.append(output_raw_dict)
    return output_attributes

def field_set_to_NoticeItem(field_set):
    item = NoticeItem()
    item['CaseID'] = field_set['CaseID']
    item['ITCNo'] = field_set['ITCNo']
    item['source_DOCNo'] = field_set['source_DOCNo']
    item['notice_DOCNo'] = field_set['notice_DOCNo']
    item['Year'] = field_set['Year']
    item['Month'] = field_set['Month']
    item['Date'] = field_set['Date']
    item['ProducerID'] = field_set['ProducerID']
    item['Action'] = field_set['Action']
    item['source_AD_CVD'] = field_set['source_AD_CVD']
    item['notice_AD_CVD'] = field_set['notice_AD_CVD']
    item['Product'] = field_set['Product']
    item['source_Country'] = field_set['source_Country']
    item['notice_Country'] = field_set['notice_Country']
    item['source'] = field_set['source']
    item['fed_reg'] = field_set['fed_reg']
    item['Notes'] = field_set['Notes']
    item['have_table'] = field_set['have_table']
    item['have_final_result_chapter'] = field_set['have_final_result_chapter']
    item['Petitioner_and_AltNm_list'] = field_set['Petitioner_and_AltNm_list']
    item['HS_list'] = field_set['HS_list']

    return item

def field_set_to_RateItem(field_set):
    item = RateItem()
    item['RateID'] = field_set['RateID']
    item['CaseID'] = field_set['CaseID']
    item['Exporter'] = field_set['Exporter']
    item['ExpAltNm'] = field_set['ExpAltNm']
    item['Producer'] = field_set['Producer']
    item['PdAltNm'] = field_set['PdAltNm']
    item['CashDeposit'] = field_set['CashDeposit']
    item['DumpingMargin'] = field_set['DumpingMargin']
    item['SubsidyRate'] = field_set['SubsidyRate']
    item['AD_CVD'] = field_set['AD_CVD']

    return item

class NoticeSearchSpider(scrapy.Spider):
    name = 'notice_search'
    allowed_domains = ['federalregister.gov']
    # start_urls = ['http://baidu.com/']

    def start_requests(self):  # read source.txt search every line
        source_file_name = 'resource/source.csv'
        source_file = open(source_file_name, "r")
        line_number = 0
        for line in source_file.readlines():
            field_set = {}
            line_number = line_number + 1
            line.strip("\n")
            if line_number <= 1:
                continue
            # if line_number > 3:
            #     continue
            line = line.replace("\ufeff", "")
            attributes = line.split(",")
            # Orderdate = attributes[0]
            # print("line: "+str(line))
            # 把原文件已有的数据提取出来，不用再在网页上提取
            field_set["CaseID"] = ""
            field_set["ITCNo"] = attributes[2]
            field_set["DOCNo"] = attributes[3]
            field_set["source_DOCNo"] = field_set["DOCNo"]
            field_set["ProducerID"] = ""
            field_set["Action"] = ""
            field_set["CashDeposit"] = ""
            field_set["AD_CVD"] = "AD" if attributes[4] == "A" else "CVD"
            field_set['source_AD_CVD'] = field_set["AD_CVD"]
            field_set["Product"] = attributes[7].replace(",", "").replace('"', '')
            field_set["Country"] = attributes[8]
            field_set['source_Country'] = field_set["Country"]
            field_set["Notes"] = ""
            field_set["source"] = ""

            url_format = "https://www.federalregister.gov/documents/search?conditions%5Bterm%5D={DOCNo}&page={page}"
            url = url_format.format(DOCNo=field_set["DOCNo"], page=1)
            # print(url)
            meta = {
                'field_set': field_set
            }
            yield scrapy.Request(
                url=url,
                callback=self.search_page_count,
                meta=meta
            )

    def search_page_count(self, response):  # know the number of search count and then search specific page
        print("进入search_page_count")
        field_set = copy.deepcopy(response.meta['field_set'])
        DOCNo = field_set['DOCNo']
        response_html = response.body.decode()
        html_tree = etree.HTML(response_html)
        item_count_raw = html_tree.xpath("//span[@id='item-count']/text()")[0]  # 获取 搜索结果中notice数，由于一页只能显示20个，所以要分页查询
        item_count = int(item_count_raw.strip())
        print("item_count: " + str(item_count))
        page_count = item_count // 20 + 1
        print(page_count)
        url_format = "https://www.federalregister.gov/documents/search?conditions%5Bterm%5D={DOCNo}&page={page}"
        for i in range(page_count):
            url = url_format.format(DOCNo=DOCNo, page=i + 1)
            meta = {
                'field_set': field_set
            }
            yield scrapy.Request(
                url=url,
                callback=self.search_notice,
                meta=meta
            )

    def search_notice(self, response):  # find notice that match condition 找出符合条件的notice
        print("进入search_notice")
        field_set = copy.deepcopy(response.meta['field_set'])
        AD_CVD = field_set['AD_CVD']
        # Country = field_set['Country']
        response_html = response.body.decode()
        html_tree = etree.HTML(response_html)
        title_list = html_tree.xpath("//div[@class='document-wrapper']/h5/a/text()")  # 获取 贸易通告标题列表
        href_list = html_tree.xpath("//div[@class='document-wrapper']/h5/a/@href")  # 获取 贸易通告所在url列表

        if AD_CVD == "AD":
            type_checkword = "antidumping"
        else:
            type_checkword = "countervailing"



        # print("len(title_list)" + str(len(title_list)))
        for i in range(len(title_list)):
            # siying要求的逻辑
            cond1 = 1
            cond2 = 0
            title_i_lower = title_list[i].lower()
            for string in [type_checkword, "administrative", "review"]:
                if string not in title_i_lower:
                    cond1 = 0
                    break
            for string in ["final", "amended"]:
                if string in title_i_lower:
                    cond2 = 1
                    break
            if cond1 and cond2:
                meta = {
                    'field_set': field_set
                }
                field_set["source"] = href_list[i]
                yield scrapy.Request(
                    url=field_set["source"],
                    callback=self.get_data_from_notice,
                    meta=meta
                )

    def get_data_from_notice(self, response):  # get data from notice 解析notice数据
        print("进入get_data_from_notice")
        field_set = copy.deepcopy(response.meta['field_set'])
        response_html = response.body.decode()
        # try:
        response_html = re.sub(r"(&nbsp;)|(&ensp;)|(&emsp;)|(&thinsp;)|(&zwnj;)|(&zwj;)|(\u2003)|(\u2009)|(<em>)|(</em>)|( )|(<strong.*?>)|(</strong>)|(<sup>)|(</sup>)",
                               " ", response_html)
        html_tree = etree.HTML(response_html)

        hs_list = get_hs_list(response_html)
        field_set['HS_list'] = ",".join(hs_list)
        hs_list_len = len(hs_list)
        for i in range(HS_setting_len):
            if i < hs_list_len:
                field_set["HS" + str(i + 1)] = hs_list[i]
            else:
                field_set["HS" + str(i + 1)] = ""

        field_set["notice_DOCNo"] = get_docket_number(html_tree)
        Orderdate = get_year_month_date(html_tree)
        field_set["Year"] = Orderdate.split("/")[2]
        field_set["Month"] = Orderdate.split("/")[0]
        field_set["Date"] = Orderdate.split("/")[1]

        Petitioner_list = get_Petitioners(response_html)
        field_set["Petitioner_and_AltNm_list"] = ",".join(Petitioner_list)
        Petitioner_list_len = len(Petitioner_list)
        # print(Petitioner_list_len)
        for i in range(Petitioner_setting_len):
            if i < Petitioner_list_len:
                field_set["Petitioner" + str(i + 1)] = Petitioner_list[i]
                field_set["Ptner$AltNm".replace("$", str(i + 1))] = ""
            else:
                field_set["Petitioner" + str(i + 1)] = ""
                field_set["Ptner$AltNm".replace("$", str(i + 1))] = ""

        field_set["fed_reg"] = get_fed_reg(html_tree)
        field_set['ExpAltNm'] = ""
        field_set['PdAltNm'] = ""

        # 记录哪些网站两者都有用来统计对策
        if "countervailing" in field_set['source'] and "antidumping" in field_set['source']:
            field_set['notice_AD_CVD'] = "AD,CVD"
        else:
            field_set['notice_AD_CVD'] = field_set['source_AD_CVD']

        # 记录哪些网站有多个国家，这个要上github找一份国家文件了

        notice_Country = []
        country_dict = load_country()
        for word in field_set['source'].split("/")[-1].split("-"):
            if word in country_dict:
                notice_Country.append(word)
        field_set['notice_Country'] = ",".join(notice_Country)



        ## 一个公司一条记录
        table_data_rows = get_company_and_subsidy_rate_in_table(html_tree)
        field_set['have_final_result_chapter'] = 0
        if len(table_data_rows) == 0:  # 如果网页中根本没有表格
            field_set['have_table'] = 0
            # f_no_table.write(field_set["source"] + "\n")
            # print("len(table_data_rows) == 0")
            # print(field_set["source"])
            if len(get_final_result_chapter(response_html)) > 0:
                table_data_rows = get_company_and_subsidy_rate_in_final_result_chapter(response_html)
                field_set['have_final_result_chapter'] = 1
        else:
            field_set['have_table'] = 1

        field_set['CaseID'] = uuid.uuid1()
        NoticeItem_one = field_set_to_NoticeItem(field_set)
        yield NoticeItem_one

        for table_data_row in table_data_rows:
            field_set = copy.deepcopy(field_set)
            data_line_list = []
            field_set["DumpingMargin"] = table_data_row["DumpingMargin"] if "DumpingMargin" in table_data_row else ""
            field_set["Exporter"] = table_data_row["Exporter"] if "Exporter" in table_data_row else ""
            field_set["Producer"] = table_data_row["Producer"] if "Producer" in table_data_row else ""
            field_set["CashDeposit"] = table_data_row["CashDeposit"] if "CashDeposit" in table_data_row else ""
            field_set["SubsidyRate"] = table_data_row["SubsidyRate"] if "SubsidyRate" in table_data_row else ""
            field_set["valorem"] = table_data_row["valorem"] if "valorem" in table_data_row else ""

            # siying 要求的替换逻辑 如果CVD的没有SubsidyRate 却又AD的用AD的替代
            if field_set["AD_CVD"] == "CVD" and (field_set["SubsidyRate"] == ""):
                if field_set["DumpingMargin"] != "":
                    field_set["SubsidyRate"] = field_set["DumpingMargin"]
                elif field_set["CashDeposit"] != "":
                    field_set["SubsidyRate"] = field_set["CashDeposit"]
                elif field_set["valorem"] != "":
                    field_set["SubsidyRate"] = field_set["valorem"]
            if field_set["AD_CVD"] == "AD" and (field_set["DumpingMargin"] == "" or field_set["CashDeposit"] == ""):
                if field_set["SubsidyRate"] != "":
                    field_set["DumpingMargin"] = field_set["SubsidyRate"]
                elif field_set["valorem"] != "":
                    field_set["DumpingMargin"] = field_set["valorem"]

            # if field_set["AD_CVD"] == "AD":
            #     for field in field_list_AD:
            #         data_line_list.append(field_set[field].replace(",", "").replace("\n", ""))
            #     data_line = ",".join(data_line_list) + "\n"
            #     print("data_line: "+data_line)
            #     # output_AD_file.write(data_line)
            # else:
            #     for field in field_list_CVD:
            #         data_line_list.append(field_set[field].replace(",", "").replace("\n", ""))
            #     data_line = ",".join(data_line_list) + "\n"
            #     print("data_line: "+data_line)
                # output_CVD_file.write(data_line)
            field_set['RateID'] = uuid.uuid1()
            RateItem_one = field_set_to_RateItem(field_set)
            yield RateItem_one
            # print(data_line_list)
            data_line_list = []

        # except Exception as e:
        #     print("e:" + str(e))
        #     print("DOCNo: " + field_set["DOCNo"] + " error")
        #     print("source: " + field_set["source"])
        #     # output_AD_file.write(notice_url + "\n")  # 写下解析错误的url
        #     # error_count = error_count + 1