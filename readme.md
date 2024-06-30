# Read me, Login strategy: 

How logged-in user is being kept track of: 
- users that are logged-in are being tracked by the use of session and session key
- session key is named 'CURR_USER_KEY'
    
    
Logout trackers: 
- when a user presses 'log out' the function 'do_login' deletes the 'CURR_USER_KEY'
    
    
Flask's g object: 
- Flask's g object is used to store data that you want to be available during a single request. 
- Each request gets its own g object, making it a convenient place to store request-specific data 
like the current user.
    
    
Purpose of add_user_to_g:
- The purpose of this function 'add_user_to_g function' is to add the current user to the g object, 
only if the user is logged in. 
- The function checks if the 'CURR_USER_KEY' is in the session.
- If true, it queries the database for the user with that ID and sets g.user to that user. - If not, it sets g.user to None.
    
@app.before_request meaning: 
- @app.before_request is used to ensure that add_user_to_g is executed before every request. 
- This makes sure that g.user is always set to the current logged-in user (if any) before any route handler is called.
    

