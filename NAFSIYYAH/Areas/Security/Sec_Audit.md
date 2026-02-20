### Current Actions
- Get a list of steps to begin disk encryption
- Do some link analysis for surfaces of attack
### Completed Actions
- How to encrypt a drive to make it innacessible to any malign entity who would seek to access it's secrets.
### Notes
Encrypting a Linux drive, especially an existing one, is a critical operation that, if done incorrectly, can lead to data loss. It's great that you're thinking about security!
The most common and robust method for full-disk encryption on Linux is **LUKS (Linux Unified Key Setup)**. LUKS provides a standard for disk encryption that allows for multiple user passphrases, key revocation, and other advanced features.
There are two main scenarios for encrypting a Linux drive:
1. **During a New Linux Installation (Recommended for ease and safety):**
	This is by far the easiest and safest way to encrypt your drive. Most modern Linux distributions (like Ubuntu, Fedora, Debian, etc.) offer an option to encrypt your entire disk (or specific partitions) using LUKS during the installation process.
	**General Steps for New Installation:**
	- Boot from your Linux distribution's installation media (USB drive or DVD).
	- During the installation wizard, when you reach the "Installation type" or "Disk partitioning" step, look for options like:
		- "Erase disk and install Linux" with a checkbox for "Encrypt the new Linux installation for security."
		- "Something else" or "Manual partitioning," where you can manually create partitions and select "Encrypt" or "LUKS" for your root (`/`) and swap partitions.
	- You will be prompted to set a strong passphrase for your LUKS volume. **Remember this passphrase!** Without it, your data will be inaccessible.
	- The installer will then proceed to set up the encrypted partitions and install the operating system.
2. **Encrypting an Existing Linux Installation (More Complex and Risky):**
	Encrypting a drive that already has an operating system and data on it is significantly more complex and carries a high risk of data loss if not performed meticulously. There are generally two approaches:
	- **Backup and Re-installation (Recommended for existing systems):**
		This is the safest approach for an existing system.
		2. **Crucial Step: Back up ALL your important data** from the drive to an external storage device. This is non-negotiable.
		3. Perform a fresh installation of your Linux distribution, following the steps for a new installation with LUKS encryption (as described above).
		4. Restore your backed-up data to the newly encrypted drive.
	- **In-place Encryption (Advanced and Very Risky):**
		This involves encrypting the drive without reinstalling the operating system. Tools like `cryptsetup` can be used, but this process is highly technical, time-consuming, and prone to errors that can lead to irreversible data loss. It typically involves shrinking existing partitions, creating new encrypted partitions, and migrating data, or using specialized tools that attempt to encrypt in place. **This method is generally not recommended for users who are not highly experienced with Linux disk management and recovery.**
**Critical Warnings:**
- **DATA LOSS:** Incorrect encryption procedures or forgetting your passphrase will result in permanent data loss. **Always back up your data before attempting any encryption.**
- **Passphrase:** Choose a strong, unique passphrase and store it securely. If you lose it, your data is gone.
- **Performance:** Encryption can introduce a slight performance overhead, though with modern hardware, this is often negligible for most users.
**Recommendation:**
If you have an existing installation, the safest path is to **back up your data and perform a fresh installation with LUKS encryption enabled during setup.**
Given the critical nature of disk encryption, I strongly advise you to:
- **Consult the official documentation** for your specific Linux distribution (e.g., Ubuntu's documentation on full disk encryption).
- **Look for up-to-date tutorials** from reputable sources.
- **Consider seeking help from an experienced Linux administrator** if you are unsure about any steps.