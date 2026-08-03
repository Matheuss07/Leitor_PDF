class User():
    def __init__(self, name, age, email):
        self.name = name
        self.age = age
        self.email = email


def create_user(name, age, email):
    return User(name, age, email)


User_dicionario = {
    "nome": "John Doe",
    "idade": 30,
    "email": "john.doe@example.com"
}
user = create_user("John Doe", 30, "john.doe@example.com")

print(user.name, User_dicionario["nome"])  
print(user.age, User_dicionario["idade"])   
print(user.email, User_dicionario["email"]) 