function fake_token_validate(request)
    -- local header = request:headers('Fake-Frinx-Token')
    -- if header ~= '' then
        print("INFO: JWT authorization is disabled. Default credentials are used!")
        request:headers('X-Auth-User-Groups', 'network-admin')
        request:headers('X-Auth-User-Roles', 'network-admin')
        request:headers('From', 'admin-user')
        request:headers('X-Tenant-Id', 'frinx')
    -- else
        -- custom_error("No permissions group", 427)
    -- end
end