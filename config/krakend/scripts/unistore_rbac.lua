local hex_to_char = function(x)
    return string.char(tonumber(x, 16))
end

local unescape = function(url)
    return url:gsub("%%(%x%x)", hex_to_char)
end

function getenv(key, fallback)
    value = os.getenv(key)
    if value == nil then
        return fallback
    end
    return value
end

function user_group_auth(request)

    -- set variables from request
    local method = request:method()
    local url = unescape(request:url())

    local headers_group = request:headers('X-Auth-User-Groups')
    local headers_role = request:headers('X-Auth-User-Roles')
    local headers_all = headers_group .. "," .. headers_role

    -- Unistore RBAC settings

    local permited_groups=getenv('UNISTORE_CONTROLLER_ADMIN_GROUP')
    local other_role=getenv("UNISTORE_OTHER_PERMITTED_ROLES",'')

    local bearer_role=getenv("UNISTORE_BEARER_ROLE",'')
    local service_role=getenv("UNISTORE_SERVICE_ROLE",'')
    local network_role=getenv("UNISTORE_NETWORK_ROLE",'')

    local bearer_node=getenv("UNISTORE_BEARER_NODE",'')
    local service_node=getenv("UNISTORE_SERVICE_NODE",'')
    local network_node=getenv("UNISTORE_NETWORK_NODE",'')
    

    local permited_all=''

    if string.match(url, "node=") then
        -- Add role to permited_group based on node parameter
        for word in string.gmatch(url, '([^/]+)') do
            if string.match(word, "node=") then
                word = string.gsub(word, "node=", "")
                print(word)
                if string.match(word, bearer_node) then
                    print(bearer_role)
                    permited_all=bearer_role..","..permited_groups 
                elseif string.match(word, service_node) then
                    print(service_role)
                    permited_all=service_role..","..permited_groups 
                elseif string.match(word, network_node) then
                    print(network_role)
                    permited_all=network_role..","..permited_groups
                end
            end
        end
    else
        permited_all=permited_groups..","..service_role..","..network_role..","..bearer_role..","..other_role
    end

    -- remove white spaces and transform to lowercase
    headers_all = headers_all:gsub("%s+", "")
    headers_all = headers_all:lower()
    permited_all = permited_all:gsub("%s+", "")
    permited_all = permited_all:lower()
    
    -- if request method is different from GET
    --  then check if user is in permitted groups


    if method ~= "GET" then
        for header_group in string.gmatch(headers_all, '([^,]+)') do
            for permited_group in string.gmatch(permited_all, '([^,]+)') do
                if header_group == permited_group then
                    return
                end
            end
        end
        print("User has no permissions for executing request, bad group")
        custom_error("No permissions group", 427)
    end
end

