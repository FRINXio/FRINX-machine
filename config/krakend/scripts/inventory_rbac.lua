

function getenv(key, fallback)
    value = os.getenv(key)
    if value == nil then
        return fallback
    end
    return value
end

function user_group_auth(request)
    -- set variables from request
    local headers_group = request:headers('X-Auth-User-Groups')
    local headers_role = request:headers('X-Auth-User-Roles')
    local headers_all = headers_group .. "," .. headers_role

    -- inventory RBAC settings
    local permited_groups=getenv('INVENTORY_ADMIN_GROUP')

    -- remove white spaces in groups
    headers_all = headers_all:gsub("%s+", "")
    headers_all = headers_all:lower()
    permited_groups = permited_groups:gsub("%s+", "")
    permited_groups = permited_groups:lower()
    
    -- if graphql query contain mutation, then check if user is admin
    local query=string.match(request:body(), "mutation")

    if query ~= nil then
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