from functools import reduce
students = [
        {"name": "Alice", "age": 20, "grades": [85, 90, 88, 92]},
        {"name": "Bob", "age": 22, "grades": [78, 89, 76, 85]},
        {"name": "Charlie", "age": 21, "grades": [92, 95, 88, 94]},
]

users = [
        {"name": "Alice", "expenses": [100, 50, 75, 200]},
        {"name": "Bob", "expenses": [50, 75, 80, 100]},
        {"name": "Charlie", "expenses": [200, 300, 550, 150]},
        {"name": "David", "expenses": [100, 200, 300, 400]},
]

orders = [
        {"order_id": 1, "customer_id": 101, "amount": 150.0},
        {"order_id": 2, "customer_id": 102, "amount": 200.0},
        {"order_id": 3, "customer_id": 101, "amount": 75.0},
        {"order_id": 4, "customer_id": 103, "amount": 100.0},
        {"order_id": 5, "customer_id": 101, "amount": 50.0},
]

# task 1
print("task 1")
age = 20
filtered_students = list(filter(lambda x: x["age"] == age, students))
print(filtered_students)

mean_grades = list(map(lambda x: sum(x["grades"]) / len(x["grades"]), students))
print(mean_grades)
print(sum(mean_grades) / len(mean_grades))

print(list(filter(lambda x: (sum(x["grades"]) / len(x["grades"])) == max(mean_grades), students)))

# task 2
print("-------------")
print("task 2")
criteria = {"name": ["Alice", "Charlie"],
            "min_expense": 100
            }
filtered_users = list(filter(lambda user: min(user["expenses"]) >= criteria["min_expense"], users))
print(list(filtered_users))
total_expences = map(lambda x: sum(x["expenses"]), users)
print(list(total_expences))
print(reduce(lambda x, y: x + sum(y["expenses"]), filtered_users, 0))

# task 3
print("-------------")
print("task 3")
customer_id = 101
customer_orders = list(filter(lambda x: x["customer_id"] == customer_id, orders))
print(customer_orders)
print(reduce(lambda x, y: x + y["amount"], customer_orders, 0))
print(reduce(lambda x, y: x + y["amount"], customer_orders, 0) / len(customer_orders))

