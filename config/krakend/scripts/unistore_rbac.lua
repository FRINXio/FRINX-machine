function user_group_auth(request, permited_groups)

    -- set variables from request
    local method = request:method()
    local url = request:url()

    local headers_group = request:headers('X-Auth-User-Groups')
    local headers_role = request:headers('X-Auth-User-Roles')
    local headers_all = headers_group .. "," .. headers_role

    -- Unistore RBAC settings
    local bearer_role=os.getenv("UNISTORE_BEARER_ROLE")
    local service_role=os.getenv("UNISTORE_SERVICE_ROLE")
    local network_role=os.getenv("UNISTORE_NETWORK_ROLE")

    local bearer_node=os.getenv("UNISTORE_BEARER_NODE")
    local service_node=os.getenv("UNISTORE_SERVICE_NODE")
    local network_node=os.getenv("UNISTORE_NETWORK_NODE")

    -- Add role to permited_group based on node parameter
    for word in string.gmatch(url, '([^/]+)') do
        if string.match(word, "node=") then
            word = string.gsub(word, "node=", "")
            if string.match(word, bearer_node) then
                permited_groups=permited_groups..","..bearer_role
            elseif string.match(word, service_node) then
                permited_groups=permited_groups..","..service_role
            elseif string.match(word, network_node) then
                permited_groups=permited_groups..","..network_role
            end
        end
    end

    -- remove white spaces and transform to lowercase
    headers_all = headers_all:gsub("%s+", "")
    headers_all = headers_all:lower()
    permited_groups = permited_groups:gsub("%s+", "")
    permited_groups = permited_groups:lower()
    
    print(headers_all)
    -- if request method is different from GET
    --  then check if user is in permitted groups
    if method ~= "GET" then
        for header_group in string.gmatch(headers_all, '([^,]+)') do
            for permited_group in string.gmatch(permited_groups, '([^,]+)') do
                if header_group == permited_group then
                    return
                end
            end
        end
        print("User has no permissions for executing request, bad group")
        custom_error("No permissions group", 427)
    end
end


