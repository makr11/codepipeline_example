import logging

def main(event, context):
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Log some output
    logging.info("This is a log message")
    
    # Your code here
    
    return "Lambda function executed successfully"
