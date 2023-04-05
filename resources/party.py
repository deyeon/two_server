from flask import request
from flask_restful import Resource
from mysql.connector.errors import Error
from mysql_connection import get_connection
from flask_jwt_extended import jwt_required,get_jwt_identity
from utils import check_password, hash_password

class partySearch(Resource):
    def post(self) :
        data = request.get_json()
        
        page = request.args.get('page')
        pageCount = int(page) * 10
        
        if data is None :
            return {'error':'서버 전송 데이터를 확인하세요.'},400
        
        try :
            connection = get_connection()

            query = '''select pb.*,count(member) as memberCnt 
                    from partyBoard pb left join party p 
                    on pb.partyBoardId = p.partyBoardId 
                    where pb.title like "%'''+data['keyword']+'''%" or pb.service like "%'''+data['service']+'''%"
                    group by partyBoardId
                    limit '''+str(pageCount)+''',10 ; '''
            cursor = connection.cursor(dictionary=True)

            cursor.execute(query)

            partyList = cursor.fetchall()

            i = 0
            for row in partyList :
                partyList[i]['createdAt'] = row['createdAt'].isoformat()
                partyList[i]['finishedAt'] = row['finishedAt'].isoformat()
                i=i+1
            cursor.close()
            connection.close()
        except Error as e :
            print(str(e))
            cursor.close()
            connection.close()
            return {'error':str(e)},500
        
        return {'result': 'success','partyList':partyList},200
            
                

class partyBoard(Resource) :
    @jwt_required()
    def post(self) :
        
#         {
#           "service" : "Netflix",
#           "title" : "넷플릭스 구독자 구함",
#          
#           "serviceId" : "abc@naver.com",
#           "servicePassword" : "12345",
#           "finishedAt" : "2022-03-15"
#       }
        userId = get_jwt_identity()

        data = request.get_json()

        if data is None :
            return {'error':'서버 전송 데이터를 확인하세요.'},400

        try :
            connection = get_connection()

            query = '''insert into partyBoard(service,title,userId,serviceId,servicePassword,finishedAt)
                    values(%s,%s,%s,%s,%s,%s);'''

            record = (data['service'],data['title'],userId,data['serviceId'],data['servicePassword'],data['finishedAt'])

            cursor = connection.cursor()

            cursor.execute(query,record)
            connection.commit()
            lastrowId = cursor.lastrowid

            
            cursor.close()
            connection.close()

            connection = get_connection()
            
            query = '''select pb.*,u.userEmail,u.profileImgUrl,u.nickname
            from partyBoard pb join user u 
            on pb.userId = u.id 
            where pb.partyBoardId = '''+str(lastrowId)+'''; '''            
            
            
            cursor = connection.cursor(dictionary=True)
           
            cursor.execute(query)
            
            partyObject = cursor.fetchall()
            
            cursor.close()
            connection.close()

            i = 0
            for row in partyObject :
                partyObject[i]['createdAt'] = row['createdAt'].isoformat()
                partyObject[i]['finishedAt'] = row['finishedAt'].isoformat()
                
                i+=1

            connection =get_connection()
            query = '''insert into party(captain, partyBoardId )
                    values(%s,%s);'''
            record = (userId,lastrowId)
            cursor = connection.cursor()

            cursor.execute(query,record)
            connection.commit()
            cursor.close()
            connection.close()


        except Error as e :
            print(str(e))
            
            cursor.close()
            connection.close()
            
            return {'error':str(e)},500
        
        return {'result':'success','party':partyObject[0]},200

    def get(self) : 
        page = request.args.get('page')
        pageCount = int(page) * 10
        try :
            connection = get_connection()

            query = '''select pb.*,u.userEmail,u.profileImgUrl,u.nickname
            from partyBoard pb join user u 
            on pb.userId = u.id
            order by pb.createdAt desc 
            limit '''+str(pageCount)+''',10 ; '''

            cursor = connection.cursor(dictionary=True)
            cursor.execute(query)

            partyBoard_list = cursor.fetchall()
            
            i = 0
            for row in partyBoard_list :
                partyBoard_list[i]['createdAt'] = row['createdAt'].isoformat()
                partyBoard_list[i]['finishedAt'] = row['finishedAt'].isoformat()
                i = i+ 1

            cursor.close()
            connection.close()
        except Error as e :
            print(str(e))
            cursor.close()
            connection.close()
            return {'error':str(e)},500
        
        return {'result':'success','partyBoard' : partyBoard_list
                ,'pageNum':page,
                'partyBoardSize':str(len(partyBoard_list))},200

class partyBoardUD(Resource) :
    @jwt_required()
    def put(self,partyBoardId):
#         {
#     "service" : "Netflix",
#     "title" : "넷플릭스 모집합니다.",
#    
#     "serviceId" : "rrc0777@naver.com",
#     "servicePassword" : "1234"
# }
        userId = get_jwt_identity()
        data = request.get_json()
        if data is None :
            return {'error':'서버 전송 데이터를 확인하세요.'},400
        password = hash_password(data['servicePassword'])

        try : 
            connection = get_connection()

            query = '''update partyBoard
                    set service = %s,title = %s  , serviceId = %s, servicePassword = %s
                    where partyBoardId = %s and userId = %s;'''
            record = (data['service'],data['title'],data['serviceId'],password,partyBoardId,userId)

            cursor = connection.cursor()

            cursor.execute(query,record)

            connection.commit()
            
            cursor.close()

            connection.close()

            connection = get_connection()
            
            query = '''select pb.*,u.userEmail,u.profileImgUrl,u.nickname
            from partyBoard pb join user u 
            on pb.userId = u.id 
            where pb.partyBoardId = '''+str(partyBoardId)+'''; '''            
            
            
            cursor = connection.cursor(dictionary=True)
           
            cursor.execute(query)
            
            partyObject = cursor.fetchall()
            
            cursor.close()
            connection.close()

            i = 0
            for row in partyObject :
                partyObject[i]['createdAt'] = row['createdAt'].isoformat()
                partyObject[i]['finishedAt'] = row['finishedAt'].isoformat()
                
                i+=1
        except Error as e :
            print(str(e))
            cursor.close()
            connection.close()
            return {'error':str(e)},500
        
        return {'result':'success','party':partyObject[0]},200


    @jwt_required()
    def delete(self,partyBoardId) :
        
        userId = get_jwt_identity()

        try :
            connection = get_connection()

            query = '''delete from partyBoard
                    where partyBoardId = %s and userId = %s;'''
            record = (partyBoardId,userId)
            
            cursor = connection.cursor()

            cursor.execute(query,record)

            connection.commit()

            cursor.close()

            connection.close()
        except Error as e :
            print(str(e))
            cursor.close()
            connection.close()
            return {'error':str(e)},500
        
        return {'result':'success'},200
    

class party(Resource) :
    @jwt_required()
    def post(self) :

        userId = get_jwt_identity()
        data = request.get_json()
        if data is None :
            return {'error':'서버 전송 데이터를 확인하세요.'},400
        try : 
            connection = get_connection()

            query = '''insert into party(captain , member , partyBoardId )
                    values(%s,%s,%s);'''
            record = (data['captain'],userId,data['partyBoardId'])

            cursor = connection.cursor()

            cursor.execute(query,record)

            connection.commit()

            partyId = cursor.lastrowid

            cursor.close()

            connection.close()

            connection = get_connection()

            query = '''insert into paymentDetails(partyBoardId,userId,amount,date)
                    values(%s,%s,%s,%s);'''
            record=(data['partyBoardId'],userId,data['pay'],data['finishedAt'])

            cursor = connection.cursor()

            cursor.execute(query,record)

            connection.commit()

            cursor.close()

            connection.close()

        except Error as e:
            print(str(e))

            cursor.close()

            connection.close()

            return {'error' : str(e)},500
        
        return {'result':'success'},200
    
    @jwt_required()
    def get(self) :

        userId = get_jwt_identity()
        page = request.args.get('page')
        pageCount = int(page) * 10
        try :
            connection = get_connection()

            query = '''select p.captain as userId,p.partyBoardId,p.createdAt,pb.service,pb.title,pb.serviceId,pb.servicePassword,pb.finishedAt,u.userEmail,u.profileImgUrl,u.nickname
                        from party p 
                        join partyBoard pb 
                        on p.partyBoardId = pb.partyBoardId join user u 
                        on pb.userId = u.id 
                        where member = %s 
                        limit '''+str(pageCount) + ''',10 ;'''
            record = (userId,)

            cursor = connection.cursor(dictionary=True)

            cursor.execute(query,record)

            party_list = cursor.fetchall()

            i = 0 
            for row in party_list :
                party_list[i]['createdAt'] = row['createdAt'].isoformat()
                party_list[i]['finishedAt'] = row['finishedAt'].isoformat()
                i = i + 1 
            
            cursor.close()

            connection.close()

        except Error as e :
            print(str(e))
            cursor.close()

            connection.close()
            return {'error',str(e)},500
        
        return {'result': 'success','partylist' : party_list,
                'pageNum':page,
                'partySize':str(len(party_list))},200
        
class partyD(Resource) :
    @jwt_required()
    def delete(self,partyBoardId):
        userId = get_jwt_identity()

        try :
            connection = get_connection()

            query = '''delete from party
                    where member = %s and partyBoardId = %s;'''
            record = (userId,partyBoardId)

            cursor = connection.cursor()

            cursor.execute(query,record)

            connection.commit()

            cursor.close()
            connection.close()
        except Error as e : 
            print(str(e))
            cursor.close()
            connection.close()
            return {'error',str(e)},500
        
        return {'result':'success'},200

class partycheck(Resource) :
    def get(self,partyBoardId) :
        try :
            connection = get_connection()

            query = '''select pb.partyBoardId, pb.userId,pb.service,pb.serviceId,pb.servicePassword,pb.finishedAt,u.userEmail
                    from partyBoard pb left join party p 
                    on pb.partyBoardId = p.partyBoardId left join user u
                    on p.member = u.id
                    where pb.partyBoardId = %s
; 
                        '''
            record = (partyBoardId,)

            cursor = connection.cursor(dictionary=True)

            cursor.execute(query,record) 

            partyMemberList = cursor.fetchall()
            memberlist = []
            i=0
            for member in partyMemberList :
                partyMemberList[i]['finishedAt'] = member['finishedAt'].isoformat()
                if partyMemberList[i]['userEmail'] is not None :
                    memberlist.append(partyMemberList[i]['userEmail'])
                i+=1

            cursor.close()

            connection.close()


        except Error as e :
            print(str(e))
            cursor.close()

            connection.close()
            return {'error',str(e)},500
        
        return {'result': 'success','memberCnt':len(partyMemberList),
                "memberEmail":memberlist,"service":partyMemberList[0]['service'],
                 "serviceId":partyMemberList[0]['serviceId'],"servicePassword":partyMemberList[0]['servicePassword'] ,
                 "finishedAt":partyMemberList[0]['finishedAt']},200

class partyCaptain(Resource):
    @jwt_required()
    def get(self) :
        userId = get_jwt_identity()
        page = request.args.get('page')
        pageCount = int(page) * 10
        try : 
            connection = get_connection()

            query = '''select pb.partyBoardId,pb.service,pb.title,pb.createdAt,pb.userId,pb.serviceId,pb.servicePassword,pb.finishedAt,u.userEmail,u.profileImgUrl,u.nickname,count(pd.userId) as memberCnt 
                    from paymentDetails pd
                    join partyBoard pb
                    on pd.partyBoardId = pb.partyBoardId join user u
                    on pb.userId = u.id
                    where pb.userId = %s
                    group by pb.partyBoardId
                    limit '''+str(pageCount) + ''',10 ;'''
            record = (userId,)

            cursor = connection.cursor(dictionary=True)

            cursor.execute(query,record)

            captainparty = cursor.fetchall();

            cursor.close()

            connection.close()

            i = 0 
            for row in captainparty :
                captainparty[i]['createdAt'] = row['createdAt'].isoformat()
                captainparty[i]['finishedAt'] = row['finishedAt'].isoformat()
                i+=1
            
        except Error as e :
            print(str(e))
            cursor.close()
            connection.close()
            return {'error',str(e)},500
        
        return {'result':'success','partylist':captainparty},200
