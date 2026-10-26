// The notice readers see on a locked writeup. Edit the wording here; every
// locked post uses it. Placeholders are filled in from each post's lock settings:
//   {platform} — e.g. HackTheBox, TryHackMe (set per post in the editor)
//   {hint}     — what the password is, e.g. "the root flag"
export const LOCK_NOTICE = {
  title: 'This writeup is locked',
  paragraphs: [
    'The box or challenge covered here is still active on {platform}. ' +
      "Out of respect for {platform}'s policy on active content, " +
      'this writeup stays password-protected until it retires.',
    'Already pwned it? The password is {hint}.',
    'Once it retires, this post will be unlocked for everyone. Happy hacking!',
  ],
}

export const DEFAULT_LOCK = {
  platform: 'HackTheBox',
  hint: 'the root flag',
}

// Suggestions in the editor's platform field. Any other name can be typed in.
export const LOCK_PLATFORMS = [
  'HackTheBox',
  'TryHackMe',
  'OffSec Proving Grounds',
  'PortSwigger Web Security Academy',
  'VulnHub',
  'Root-Me',
]

export function fillLockNotice(text, { platform, hint }) {
  return text
    .replaceAll('{platform}', platform || DEFAULT_LOCK.platform)
    .replaceAll('{hint}', hint || DEFAULT_LOCK.hint)
}
