function user_group_auth(request, permited_groups)
    local method = request:method()
    local headers_group = request:headers('X-Auth-User-Groups')
    local headers_role = request:headers('X-Auth-User-Roles')

    local headers_all = headers_group .. "," .. headers_role
    -- remove white spaces in groups
    headers_all = headers_all:gsub("%s+", "")
    headers_all = headers_all:lower()
    permited_groups = permited_groups:gsub("%s+", "")
    permited_groups = permited_groups:lower()
    
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


