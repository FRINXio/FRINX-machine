function fake_token_validate(request)
    -- local header = request:headers('Fake-Frinx-Token')
    -- if header ~= '' then
        print("INFO: JWT authorization is disabled. Default credentials are used!")
        request:headers('X-Auth-User-Groups', os.getenv("ADMIN_ACCESS_ROLE"))
        request:headers('X-Auth-User-Roles',  os.getenv("ADMIN_ACCESS_ROLE"))
        request:headers('From', 'admin-user')
        request:headers('X-Tenant-Id', os.getenv("AZURE_TENANT_ID"))
    -- else
        -- custom_error("No permissions group", 427)
    -- end
end