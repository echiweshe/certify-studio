# How to Change PostgreSQL Password

## Method 1: Using pgAdmin (Easiest)

1. Open pgAdmin 4
2. Connect to your PostgreSQL server
3. Right-click on "Login/Group Roles" → "postgres"
4. Select "Properties"
5. Go to the "Definition" tab
6. Enter your new password in the "Password" field
7. Click "Save"

## Method 2: Using SQL Command

1. Connect to PostgreSQL as superuser:
   ```bash
   psql -U postgres
   ```

2. Run this command:
   ```sql
   ALTER USER postgres PASSWORD 'your_new_password';
   ```

3. Exit:
   ```sql
   \q
   ```

## Method 3: Using Command Line

```bash
# Windows
psql -U postgres -c "ALTER USER postgres PASSWORD 'your_new_password';"

# Or interactive
psql -U postgres
postgres=# \password
Enter new password: [type new password]
Enter it again: [confirm password]
postgres=# \q
```

## After Changing Password

1. Update `.env.postgresql`:
   ```
   DATABASE_PASSWORD=your_new_password
   ```

2. Update `.env` by running:
   ```bash
   cd scripts/database
   python update_env.py
   ```

3. Restart your backend

## Security Best Practices

1. **Use a strong password** with:
   - At least 12 characters
   - Mix of uppercase/lowercase letters
   - Numbers and special characters
   - No dictionary words

2. **Never commit passwords** to git:
   - Keep `.env` and `.env.postgresql` in `.gitignore`
   - Use environment variables in production
   - Consider using a password manager

3. **Rotate passwords regularly**
   - Change passwords every 90 days
   - Don't reuse old passwords

4. **Use different passwords** for different environments:
   - Development
   - Staging
   - Production

## Example Strong Password

Instead of: `password123`
Use something like: `Cert!fy$tud10_2025@PG`

## Connection String Format

After changing password, your connection string should be:
```
postgresql://postgres:your_new_password@localhost:5432/Certify Studio Local
```

Special characters in passwords need URL encoding:
- `@` → `%40`
- `$` → `%24`
- `&` → `%26`
- `#` → `%23`
