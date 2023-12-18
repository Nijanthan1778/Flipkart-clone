from flask import Flask,render_template,request,redirect,url_for,session,jsonify
from bson.objectid import ObjectId
from bson.decimal128 import Decimal128
import requests,pymongo,json,math
from flask_wtf import FlaskForm
from wtforms import StringField,DecimalField,PasswordField,SubmitField,EmailField,IntegerField
from wtforms.validators import ValidationError,InputRequired,Length,EqualTo,Email
from flask_bcrypt import Bcrypt

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


from flask_login import LoginManager,UserMixin,login_user,logout_user,login_required,current_user


app=Flask(__name__)
app.secret_key="key"
bcrypt=Bcrypt(app)
login_manager=LoginManager()
login_manager.init_app(app)


   
userProfile=0
userId=0
client = pymongo.MongoClient("mongodb://localhost:27017")
db=client["flipkart"]

class user_register():
   def __init__(self,username,mobile_no,email,delivery_address):
      self.username=username
      self.mobile_no=mobile_no
      self.email=email
      self.delivery_address=delivery_address
      self.hashed_password=""

   @property
   def password(self):
      return self.hashed_password
   
   @password.setter
   def password(self,password_to_hash):
    self.hashed_password=bcrypt.generate_password_hash(password_to_hash).decode("utf-8")

class user_login(UserMixin):
   def __init__(self,user_data):
      self.id=user_data["_id"]
      self.username=user_data["username"]
      self.mobile_no=user_data["mobile_no"]
      self.email=user_data["email"]
      self.delivery_address=user_data["delivery_address"]

@login_manager.user_loader
def user_loader(userID):
   col=db["users"]
   data=col.find_one({"_id":ObjectId(userID)})    
   if data:
      return user_login(data)  
   return None

         

class RegisterForm(FlaskForm):
   def validate_mobile_no(self,mobile_no_to_validate):
      col=db["users"]
      user=col.find_one({"MobileNo":mobile_no_to_validate.data})
      if user:
         raise ValidationError("User already Exists ")
      
   def validate_email(self,email_to_validate):
      col=db["users"] 
      user=col.find_one({"Email":email_to_validate.data})  
      if user:
         raise ValidationError("User already Exists ")
      
   username=StringField("Username",validators=[InputRequired(),Length(min=5,max=30)])
   mobile_no=IntegerField("Mobile No",validators=[InputRequired()])
   email=EmailField("Email Address",validators=[InputRequired(),Email()])
   address=StringField("Delivery Address",validators=[InputRequired()])
   password=PasswordField("Create Password",validators=[InputRequired(),Length(min=5,max=15)])
   confirm_password=PasswordField("Confirm Password",validators=[EqualTo("password")])
   submit=SubmitField("Sign up")


class LoginForm(FlaskForm):
   def validate_mobile_no(self,mobile_no_to_validate):
      col=db["users"]
      user=col.find_one({"mobile_no":mobile_no_to_validate.data})
      if not user:
         raise ValidationError("User not found")
      else:        
         if not bcrypt.check_password_hash(user["password"],self.password.data):
            raise ValidationError("Incorrect Password")
         
   mobile_no=IntegerField("Mobile No",validators=[InputRequired()])
   password=PasswordField("Password",[InputRequired()])
   submit=SubmitField("Login")
   hashed_password=bcrypt
   

@app.route("/",methods=["POST","GET"])
def home():
   col_mobiles=db["mobiles"]
   data_mobiles=col_mobiles.find()

   col_shoes=db["shoes"]
   data_shoes=col_shoes.find()

   col_laptops=db["laptops"]
   data_laptops=col_laptops.find()
   
   return render_template("home.html",dmobiles=data_mobiles,dshoes=data_shoes,dlaptops=data_laptops,userProfile=userProfile)



@app.route("/home2/<string:category>/<string:id>",methods=["POST","GET"])
def home2(category,id):
    col=db[category]
    data=col.find({"_id":ObjectId(id)})
    return render_template("home2.html",d=data)
  


@app.route("/mobiles/<string:id>",methods=["POST","GET"])
def mobiles(id):
   col=db["mobiles"]
   data=col.find({"_id":{"$ne":ObjectId(id)}})
   data2=col.find({"_id":ObjectId(id)})
   return render_template("mobiles.html",d=data,d2=data2,userProfile=userProfile)
   

@app.route("/mobilesdata",methods=["POST","GET"])
def mobilesdata():
    if request.method=="POST":
      data=request.json
      col=db["mobiles"]
      col.insert_one(data)  
    return jsonify(data)


@app.route("/shoes/<string:id>",methods=["POST","GET"])
def shoes(id):
   col=db["shoes"]
   data=col.find({"_id":{"$ne":ObjectId(id)}})
   data2=col.find({"_id":ObjectId(id)})
   return render_template("shoes.html",d=data,d2=data2,userProfile=userProfile)


@app.route("/shoesdata",methods=["POST","GET"])
def shoesdata():
    if request.method=="POST":
      data=request.json
      col=db["shoes"]
      col.insert_one(data)  
    return jsonify(data)


@app.route("/laptops/<string:id>",methods=["POST","GET"])
def laptops(id):
   col=db["laptops"]
   data=col.find({"_id":{"$ne":ObjectId(id)}})
   data2=col.find({"_id":ObjectId(id)})
   return render_template("laptops.html",d=data,d2=data2,userProfile=userProfile)
   

@app.route("/laptopsdata",methods=["POST","GET"])
def laptopsdata():
    if request.method=="POST":
      data=request.json
      col=db["laptops"]
      col.insert_one(data)  
    return jsonify(data)


@app.route("/addtocart/<string:category>/<string:id>",methods=["POST","GET"])
def addtocart(category,id): 
 if userId:
   #### getting cartitem data for current user to display in addtocart page 
   col=db["cart_items"]
   data=col.find({"userId":userId}).sort({"_id":-1})
   cart_items_list=[]
   for document in data:
      cart_items_list.append(document)


   col2=db[category]
   if category!="?" and id!="?":
      data2=col2.find_one({"_id":ObjectId(id)})
      for cart_item in cart_items_list:
        if cart_item["id"]==id:
         break
      else:   
        col.insert_one({"id":str(data2["_id"]),"ProductName":data2["ProductName"],"Price":data2["Price"],"Description":data2["Description"],"ProductImage":data2["ProductImage"],"Category":data2["Category"],"No_of_items":1,"userId":userId}) 
  
   
   price=0
   totalProducts=0
   col3=db["cart_items"]
   data3=col3.find({"userId":userId}).sort({"_id":-1})
   cart_items_list2=[]
   for item in data3:
      cart_items_list2.append(item)

   for item in cart_items_list2:
      price=price+int(item["No_of_items"])*int(item["Price"].replace(",",""))
      totalProducts=totalProducts+int((item["No_of_items"]))
   discount=math.floor(price*0.2)
   total=price-discount   
     
   return render_template("addtocart.html",d=cart_items_list2,price=price,discount=discount,total=total,totalProducts=int(totalProducts),userProfile=userProfile)
 return redirect(url_for('login'))
 

@app.route("/addotocartplus/<string:category>/<string:id>")
def addtocartplus(category,id):
   col=db["cart_items"]
   data=col.find_one({"id":id})
   col.find_one_and_update({"id":id},{"$set":{"No_of_items":int(data["No_of_items"]+1)}})
   return redirect(url_for("addtocart",category="?",id="?"))

@app.route("/addotocartminus/<string:category>/<string:id>")
def addtocartminus(category,id):
   col=db["cart_items"]
   data=col.find_one({"id":id})
   if int(data["No_of_items"])>1:
    col.find_one_and_update({"id":id},{"$set":{"No_of_items":int(data["No_of_items"]-1)}})
   return redirect(url_for("addtocart",category="?",id="?"))

@app.route("/removeProduct/<string:category>/<string:id>",methods=["POST","GET"])
def removeProduct(category,id):
   col=db["cart_items"]
   col.delete_one({"id":id})
   return redirect(url_for('addtocart',category="?",id="?"))


@app.route("/login",methods=["POST","GET"])
def login():
   form=LoginForm()
   if request.method=="POST":
      if form.validate_on_submit:   
         mobile_no=form.mobile_no.data
         password=form.password.data
         col=db["users"]
         data=col.find_one({"mobile_no":mobile_no})
         if data and bcrypt.check_password_hash(data["hashed_password"],password):
            user_to_login=user_login(data)
            login_user(user_to_login)
            global userProfile
            userProfile=current_user.username[:1].upper()
            global userId
            userId=current_user.id
            return redirect(url_for("home"))
      
   return render_template("login.html",form=form,userProfile=userProfile)   


@app.route("/signup",methods=["POST","GET"])
def signup():
   form=RegisterForm()
   if request.method=="POST":
      if form.validate_on_submit:
        username=form.username.data
        mobile_no=form.mobile_no.data
        email=form.email.data
        address=form.address.data
        password=form.password.data
        new_user=user_register(username,mobile_no,email,address)   
        new_user.password=password
        col=db["users"]
        col.insert_one(new_user.__dict__)

        user_to_login=col.find_one({"username":username,"mobile_no":mobile_no,"email":email,"delivery_address":address})
        new_user_login=user_login(user_to_login)
        login_user(new_user_login)
        global userProfile
        userProfile=current_user.username[:1].upper()
        global userId
        userId=current_user.id
        return redirect(url_for("home"))
   return render_template("signup.html",form=form,userProfile=userProfile)   


@app.route("/logout")
@login_required
def logout():
   logout_user()
   global userId
   userId=0
   global userProfile
   userProfile=0
   print("logged out")
   return redirect(url_for('home'))

@app.route("/removeAccount")
@login_required
def removeAccount():
   col=db["users"]
   col.delete_one({"_id":ObjectId(current_user._id)})
   logout_user()
   global userId
   userId=0
   global userProfile
   userProfile=0
   return redirect(url_for('home'))


          

         

if "__main__"==__name__:
    app.run(debug=True)



