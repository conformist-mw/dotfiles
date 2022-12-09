encrypt:
	ansible-vault encrypt secrets.enc --vault-password-file vault-password-file

decrypt:
	ansible-vault decrypt secrets.enc --vault-password-file vault-password-file

deploy-rpi:
	ansible-playbook rpi.yml -e @secrets.enc --vault-password-file vault-password-file
