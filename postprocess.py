"""
@Desc: Post process of results.
@Date: 2024-12-12.
"""

def check_substrings(main_string, substrings):
    """
    Check if the main string contains any specified substrings.
    
    Params:
    - main_string (str): Main string, search for substrings within it.
    - substrings (list of str): List of substrings to be retrieved.
    
    Returns:
    - List of substrings included in the main string.
    """
    found = []
    for substring in substrings:
        if substring in main_string:
            found.append(substring)
    return found


def response_format(query, response):
    
    response = response.split('Final Answer: ')[-1].strip()
    response = response.split('list[number]:')[-1].strip()
    response = response.split('list[number]')[-1].strip()
    response = response.split('list[category]')[-1].strip()
    response = response.split('list[category]:')[-1].strip()
    response = response.split('list[url]')[-1].strip()
    response = response.split('list[url]:')[-1].strip()
    response = response.split('\n')[0].strip()
    try:
        response = eval(response)
    except Exception as e:
        print(f'Error occur: {e}')
        pass

    if isinstance(response, float):
        return response
    elif isinstance(response, int):
        return response
    else:
        # Check the types of elements in the list: int, float, string
        if isinstance(response, list):
            new_response = []
            for ele in response:
                if isinstance(ele, list):
                    ele = str(ele)
                new_response.append(ele)
            response = new_response

        # Bool format
        try:
            lower_response = response.lower()
            if lower_response in ['true', 'yes']:
                new_response = True
                return new_response
            if lower_response in ['false', 'wrong', 'no']:
                new_response = False
                return new_response
        except:
            pass
        

        # Remove quotation marks before and after the string
        # if response.startswith("'") and response.endswith("'"):
        #     new_response = response[1:-1]
        #     return new_response

        # if response.startswith('"') and response.endswith('"'):
        #     new_response = response[1:-1]
        #     return new_response

        # if response.startswith('‘') and response.endswith('’'):
        #     new_response = response[1:-1]
        #     return new_response
        # if response[0] in ['"', '\'', '’', '‘']:
        #     response = response[1:]
        # if response[-1] in ['"', '\'', '’', '‘']:
        #     response = response[:-1]
        # if isinstance(response, tuple):
        #     response = list(response)

        # 0116 New rule: If the query starts with a list and no numbers appear in the query, force deduplication
        query = query.lower()
        if query.startswith('list') and isinstance(response, list) and 'count' not in query and ('repeat' not in query or 'unique' in query or 'different' in query):
            found = check_substrings(query, ['1', '2', '3', '4', '5', '6', '7', '8', '9','10', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten'])
            if len(found) == 0:
                response = list(set(response))

        return response


if __name__ == "__main__":
    res = "['Ciudadanos', [], 'I am undeceided', 'Podemos', 'PP', 'PP']"
    res = "[]"
    # res = "'2.687'" 
    # res = "list[category]\n4, 3, 5, 7" 
    query = 'List the 5 smallest deviations from the expected death rate in relation to diseases of the heart.'
    n_res = response_format(query, res)
    print(n_res)
