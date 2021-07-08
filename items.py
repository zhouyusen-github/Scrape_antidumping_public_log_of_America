# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ScrapeAntidumpingPublicLogOfAmericaItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class NoticeItem(scrapy.Item):
    table = "notice"
    CaseID = scrapy.Field()
    ITCNo = scrapy.Field()
    source_DOCNo = scrapy.Field()
    notice_DOCNo = scrapy.Field()
    Year = scrapy.Field()
    Month = scrapy.Field()
    Date = scrapy.Field()
    ProducerID = scrapy.Field()
    Action = scrapy.Field()
    source_AD_CVD = scrapy.Field()
    notice_AD_CVD = scrapy.Field()
    Product = scrapy.Field()
    source_Country = scrapy.Field()
    notice_Country = scrapy.Field()
    source = scrapy.Field()
    fed_reg = scrapy.Field()
    Notes = scrapy.Field()
    have_table = scrapy.Field()
    have_final_result_chapter = scrapy.Field()
    Petitioner_and_AltNm_list = scrapy.Field()
    HS_list = scrapy.Field()


class RateItem(scrapy.Item):
    # define the fields for your item here like:
    table = "rate"
    RateID = scrapy.Field()
    CaseID = scrapy.Field()
    Exporter = scrapy.Field()
    ExpAltNm = scrapy.Field()
    Producer = scrapy.Field()
    PdAltNm = scrapy.Field()
    CashDeposit = scrapy.Field()
    DumpingMargin = scrapy.Field()
    SubsidyRate = scrapy.Field()
    DOCNo = scrapy.Field()
    AD_CVD = scrapy.Field()
