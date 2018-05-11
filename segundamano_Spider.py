
import scrapy
import json
import codecs
import re
#from scrapy_splash import SplashRequest
from ..items import NewSegundamanoItem 
#import urllib.request ,  urllib.error
from scrapy.spiders import CrawlSpider

# lien au site https://www.segundamano.mx/anuncios/mexico/inmuebles
class SegundamanoJsonSpider(scrapy.Spider):
    name = 'segundamano_Mai_first'
    allowed_domains = ['webapi.segundamano.mx', 'segundamano.mx']
    handle_httpstatus_list = [301, 302, 502, 200]
    download_delay = 0
    download_timeout = 280

    start_urls = ['https://webapi.segundamano.mx/nga/api/v1/public/klfst?lang=es&category=1000&company_ad=1&lim=36',
    'https://webapi.segundamano.mx/nga/api/v1/public/klfst?lang=es&category=1000&company_ad=0&lim=36']


	#lien pour ancien spider sans categorie 1 et 0
    #'https://webapi.segundamano.mx/nga/api/v1/public/klfst?lang=es&category=1000&lim=36'
    def correct(self,champ):

        return str(champ).replace('\r', ' ').replace('\n', ' ').replace('\t', ' ').replace(';', ' ').replace('\"', ' ')


    #@property
    def parse(self, response):#120,840 anuncios en Venta y renta de inmuebles en México 12_02

        #en va utiliser cette comande " .decode('utf8') " car en une lecture de json avec le python 3.5 
        #si il est python 2  utilisation direct de response.body sans  le decodage car il est une str direct n est pas byte comme le python 3.5
        body_json=response.body.decode('utf8')
        data = json.loads(body_json)
        for jsonresponse in data.get('list_ads',[]):
            myItem = NewSegundamanoItem()
            #myItem['SIRET'] = data.get('Result')[0].get('Sections')[1].get('Tags')[18].get('Value')
            #key = data.get('Result')[0].get('Sections')[1].get('Tags')[18].get('Key')
            myItem['ANNONCE_LINK'] = self.correct(jsonresponse.get('ad').get('share_link'))

            ad_id = jsonresponse.get('ad').get('ad_id')
            link = myItem['ANNONCE_LINK'].split('/')
            myItem['ID_CLIENT'] = self.correct(link[-1])

            myItem['ANNONCE_TEXT'] = self.correct(jsonresponse.get('ad').get('body'))
            nom = self.correct(jsonresponse.get('ad').get('subject'))
            myItem['NOM']=nom

            achat_loc =self.correct( jsonresponse.get('ad').get('category').get('label'))  #change it with one or 2 later
            if achat_loc=='Desarrollos inmobiliarios':
                myItem['NEUF_IND']='Y'
            else:
                myItem['NEUF_IND']='N'

            
            if achat_loc=='Venta inmuebles' or achat_loc=='Desarrollos inmobiliarios':
                myItem['ACHAT_LOC']=1

            elif achat_loc=='Renta inmuebles':
                myItem['ACHAT_LOC']=2

            elif achat_loc=='Rentas vacacionales':
                myItem['ACHAT_LOC']=8

            elif achat_loc=='Traspasos':
                myItem['ACHAT_LOC']=1


            else:
                myItem['ACHAT_LOC']=achat_loc

            categorie = ""
            try:
                categorie= self.correct(jsonresponse.get('ad').get('ad_details').get('estate_type').get('single').get('label') )
            except:
                pass

 
            if len(categorie)>0 and str(categorie)!="0" and achat_loc!='Desarrollos inmobiliarios':
                myItem['CATEGORIE']=categorie
            else:
                categorie="Otros"
                if categorie=="Otros" and achat_loc=='Desarrollos inmobiliarios':
                    categorie=achat_loc


                if categorie=="Otros":
                    departamento=["departamento","apartamento","edificio","deptos","depas"]
                    for depart in departamento:
                        if str(depart).upper() in str(nom).upper()  :
                            categorie="Departamentos"
                        
                
                if categorie == "Otros":
                    casa="casa"
                    if str(casa).upper() in str(nom).upper():
                        categorie="Casas"


                if categorie == "Otros":

                    terreno=["terreno","hectárea","hectarea","lote"]
                    for terr in terreno :
                        if str(terr).upper() in str(nom).upper() :
                            categorie="Terrenos"
                            
                
                if categorie == "Otros":

                    locales=["local","consultorio","oficina"]
                    for local in locales:
                        if str(local).upper() in str(nom).upper():
                            categorie="Oficinas/locales"
                            

                if categorie =="Otros" :
                    bodegas=["bodega","nave"]
                    for bodega in bodegas:
                        if str(bodega).upper() in str(nom).upper():
                            categorie="Bodegas"

                            
                    
                myItem['CATEGORIE']=categorie

#            myItem['Maison_APT'] = #fill it with myItem['CATEGORIE']#change it with 1 or 2 later
            piece=""
            try:
                piece = self.correct(jsonresponse.get('ad').get('ad_details').get('rooms').get('single').get('label'))
            except:
                pass
            if "más" in piece:
                piece = re.findall("([0-9]+)",piece)
                myItem['PIECE']=int(piece[0])+1
            else:
                myItem['PIECE']=piece
            #try:
            #    myItem['PAYS_AD'] = self.correct(jsonresponse.get('ad').get('ad_details').get('size').get('single').get('label'))
            #except:
            #    pass

            try:
                myItem['M2_TOTALE'] = float(self.correct(jsonresponse.get('ad').get('ad_details').get('size').get('single').get('code') ))#its M2_TOTALE without m2
            except:
                pass
            try:
                myItem['PHOTO'] = self.correct(len(jsonresponse.get('ad').get('images')))
            except:
                myItem['PHOTO'] = 0
            devise=""
            prix=""
            try:
                devise= self.correct(jsonresponse.get('ad').get('list_price').get('currency'))
                prix= self.correct(jsonresponse.get('ad').get('list_price').get('price_value'))

            except:
                pass

            #if devise=="MXN":
            #    myItem['PRIX'] =float(prix)/19
            #else:
            myItem['PRIX'] =str(prix)+str(devise)

            try:
                annonce_date = self.correct(jsonresponse.get('ad').get('list_time').get('label'))
            except:
                pass

            if annonce_date:
                if 'feb' in annonce_date:
                    cc = annonce_date.split(' ')
                    myItem['ANNONCE_DATE'] = '2018-02-'+cc[0]+' '+cc[-1]+':00'
                elif 'enero' in annonce_date:
                    cc = annonce_date.split(' ')
                    myItem['ANNONCE_DATE'] = '2018-01-'+cc[0]+' '+cc[-1]+':00'
                elif 'dic' in annonce_date:
                    cc = annonce_date.split(' ')                                                                                                               
                    myItem['ANNONCE_DATE'] = '2017-12-'+cc[0]+' '+cc[-1]+':00'
                elif 'oct' in annonce_date:
                    cc = annonce_date.split(' ')
                    myItem['ANNONCE_DATE'] = '2017-10-'+cc[0]+' '+cc[-1]+':00'
                elif 'nov' in annonce_date:
                    cc = annonce_date.split(' ')
                    myItem['ANNONCE_DATE'] = '2017-11-'+cc[0]+' '+cc[-1]+':00'
                elif 'marzo' in annonce_date:
                    cc = annonce_date.split(' ')
                    myItem['ANNONCE_DATE'] = '2018-03-'+cc[0]+' '+cc[-1]+':00'

                else:
                    myItem['ANNONCE_DATE']=annonce_date

            province=""
            ville=""
            try:
                province = self.correct(jsonresponse.get('ad').get('locations')[0].get('label'))
                myItem['PROVINCE']=province
            except:
                pass

            try:
                ville = self.correct(jsonresponse.get('ad').get('locations')[0].get('locations')[0].get('label'))
                myItem['VILLE']=ville
            except:
                pass
            try:
                myItem['QUARTIER'] = self.correct(jsonresponse.get('ad').get('locations')[0].get('locations')[0].get('locations')[0].get('label'))
            except:
                pass
            try:
                myItem['SELLER_TYPE'] = self.correct(jsonresponse.get('ad').get('type').get('label')) #in reality this is the ACHAT_LOCATION change it later with 1 or 2
            except:
                pass
            try:
                myItem['AGENCE_NOM'] =self.correct( jsonresponse.get('ad').get('user').get('account').get('name'))
            except:
                pass

#--------------------------------------
            myItem['FROM_SITE']='segundamano'
         
            full_url_telephone = 'https://webapi.segundamano.mx/nga/api/v1/public/klfst/'+myItem['ID_CLIENT']+'/phone?lang=es' 
            
            url_list_json=response.url
            #print ("***",url_list_json)
            if ("company_ad=1" in str(url_list_json)):
                #profisionel Y
                myItem['PRO_IND']='Y'
                myItem['SELLER_TYPE']="Profesional"
            else:
                #particular =private = N
                myItem['SELLER_TYPE']="Particular"

                myItem['PRO_IND']='N'

            shop_id=""
            try:
                shop_id = self.correct(jsonresponse.get('ad').get('shop_id')) #pour distinger si il es pro alors ce id existe et si il est vide alors private
            except:
                print ("not found")
            if shop_id == "None" or shop_id=="":

                myItem['MINI_SITE_ID']=""
                myItem['MINI_SITE_URL']=""

                #-------  agence ville et agence departement est le meme que adress Ubicación 
                myItem['AGENCE_VILLE']=ville
                myItem['AGENCE_DEPARTEMENT']=province


                try:
                    request_adress=scrapy.Request(url=full_url_telephone,callback=self.detail_page,dont_filter=True) 
                    request_adress.meta["myItem"]=myItem
                    yield request_adress
                    #------------------------json vers les numero telephone  direct-------

                except:
                    print("error ")
            else:

                myItem['MINI_SITE_ID']=shop_id
                myItem['MINI_SITE_URL']="https://www.segundamano.mx/tiendas/"+str(shop_id)

#------------------------------------json vers le adress agence pour prendre le code de adress agence 
#et en recherche adresse corespondant a se code dans une autre json puis extraction du numero telephone de une final requeset json 

                json_adress_agence="https://webapi.segundamano.mx/shops/api/v1/public/shops/"+str(shop_id)


                try:
                    request_adress=scrapy.Request(url=json_adress_agence,callback=self.adress_agence_code,dont_filter=True) 
                    request_adress.meta["myItem"]=myItem
                    request_adress.meta["full_url_telephone"]=full_url_telephone
                    yield request_adress
                except:
                    print("error")
                #cette request est vers le page json qui en va attraper le code de l adrresss



           
#-/*/////////////////////////Next page 
        next_page=""
        next_id = data.get('next_page',[])

        if myItem['PRO_IND']=='Y':

            next_page = 'https://webapi.segundamano.mx/nga/api/v1/public/klfst?lang=es&category=1000&company_ad=1&o='+str(next_id)
        if myItem['PRO_IND']=='N':
            next_page = 'https://webapi.segundamano.mx/nga/api/v1/public/klfst?lang=es&category=1000&company_ad=0&o='+str(next_id)
        

        if next_page:
            req = scrapy.Request(next_page)#,  callback=self.parse)
            yield req


            
#-------------------------agence adresss code  ---------------------------------------


    def adress_agence_code(self,response):
        body_json=response.body.decode('utf8')
        data=json.loads(body_json)
        myItem=response.meta['myItem']
        full_url_telephone=response.meta['full_url_telephone']
        #try:
        
        agence_code_region=data.get('locations')[0].get('code')                               
        agence_code_municipality=data.get('locations')[0].get('locations')[0].get('code')    

        agence_code_complet="https://webapi.segundamano.mx/nga/api/v1.1/public/regions?lang=es&depth=1&from=region:"+str(agence_code_region)
    
        request_adress_complet=scrapy.Request(url=agence_code_complet,callback=self.adress_agence_complet,dont_filter=True) 
        request_adress_complet.meta["agence_code_municipality"]=str(agence_code_municipality)
        request_adress_complet.meta["agence_code_region"]=str(agence_code_region)

        request_adress_complet.meta["myItem"]=myItem
        request_adress_complet.meta["full_url_telephone"]=full_url_telephone
        print(agence_code_municipality,"  ",agence_code_region)

    
        yield request_adress_complet


# #------------------------- remplir dans item le agence adresss complet et envoi une request pour attraper le numero telephone avec meta de lien de numero  ---------------------------------------

    def adress_agence_complet(self,response):

        print("************final***************************************")

        body_json=response.body.decode('utf8')
        data=json.loads(body_json)

        myItem=response.meta['myItem']
        agence_code_municipality=response.meta["agence_code_municipality"]
        agence_code_region=response.meta["agence_code_region"]
        full_url_telephone=response.meta["full_url_telephone"]
        i=0
        #json_agence_code_region=self.correct(data.get('code'))
        #while agence_code_region != json_agence_code_region and agence_code_municipality != json_agence_code_municipality:
        final_agence_municipality=""
        final_agence_region=""
        
        while i < int(data.get('children')): #nombre de municipality dans le region  
            json_agence_code_municipality=self.correct(data.get('locations')[i].get('code'))
            final_agence_municipality=""
            final_agence_region=""
            if agence_code_municipality == json_agence_code_municipality:

                final_agence_region=self.correct(data.get('label'))
                final_agence_municipality=self.correct(data.get('locations')[i].get('label'))
                print(agence_code_municipality,"  ",agence_code_region)
                print(final_agence_municipality," ", final_agence_region)
                break
            else:
                i=i+1
        if final_agence_municipality != "" or final_agence_region != "" :
            myItem['AGENCE_VILLE']=final_agence_municipality
            myItem['AGENCE_DEPARTEMENT']=final_agence_region
        else:
            myItem['AGENCE_VILLE']=""
            myItem['AGENCE_DEPARTEMENT']=""

        request = scrapy.Request(full_url_telephone, callback = self.detail_page)
        request.meta["myItem"] = myItem

        yield request

#**********************numero telephone *************
    def detail_page(self, response):
        body_json=response.body.decode('utf8')
        data = json.loads(body_json)
        myItem = response.meta['myItem']
        try:
            tel= self.correct(data.get('phones',[])[0].get('label'))
            tel1=""
            tel2=""
            if len(str(tel)) in[16,20]:
                tel1=tel[:int(len(tel)/2)]
                tel2=tel[int(len(tel)/2):]
                myItem['AGENCE_TEL']=tel1
                myItem['AGENCE_TEL_2']=tel2
            else:
                myItem['AGENCE_TEL']=tel

        except:
            pass
        yield myItem
