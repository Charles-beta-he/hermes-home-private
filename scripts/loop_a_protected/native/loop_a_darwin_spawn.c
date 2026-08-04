#define _DARWIN_C_SOURCE 1

#include <errno.h>
#include <fcntl.h>
#include <spawn.h>
#include <stddef.h>
#include <sys/types.h>
#include <unistd.h>

#define LOOP_A_FD_COUNT 10

#if !defined(__APPLE__)
#error "loop_a_darwin_spawn.c requires Darwin"
#endif

#if !defined(POSIX_SPAWN_CLOEXEC_DEFAULT)
#error "Darwin POSIX_SPAWN_CLOEXEC_DEFAULT is required"
#endif

__attribute__((visibility("default")))
int
loop_a_darwin_spawn(const char *executable_path,
                    char *const argv[],
                    char *const envp[],
                    const int source_fds[LOOP_A_FD_COUNT],
                    pid_t *child_pid)
{
    posix_spawn_file_actions_t actions;
    posix_spawnattr_t attributes;
    int normalized[LOOP_A_FD_COUNT];
    short flags;
    int actions_ready = 0;
    int attributes_ready = 0;
    int result = 0;
    size_t index;

    for (index = 0; index < LOOP_A_FD_COUNT; ++index) {
        normalized[index] = -1;
    }
    if (executable_path == NULL || executable_path[0] != '/' ||
        argv == NULL || argv[0] == NULL || envp == NULL ||
        source_fds == NULL || child_pid == NULL) {
        return EINVAL;
    }
    *child_pid = (pid_t)-1;

    for (index = 0; index < LOOP_A_FD_COUNT; ++index) {
        size_t other;
        if (source_fds[index] < 0) {
            result = EINVAL;
            goto cleanup;
        }
        for (other = 0; other < index; ++other) {
            if (source_fds[index] == source_fds[other]) {
                result = EINVAL;
                goto cleanup;
            }
        }
        normalized[index] = fcntl(source_fds[index], F_DUPFD_CLOEXEC, LOOP_A_FD_COUNT);
        if (normalized[index] == -1) {
            result = errno;
            goto cleanup;
        }
    }

    result = posix_spawn_file_actions_init(&actions);
    if (result != 0) {
        goto cleanup;
    }
    actions_ready = 1;
    for (index = 0; index < LOOP_A_FD_COUNT; ++index) {
        result = posix_spawn_file_actions_adddup2(&actions, normalized[index], (int)index);
        if (result != 0) {
            goto cleanup;
        }
    }

    result = posix_spawnattr_init(&attributes);
    if (result != 0) {
        goto cleanup;
    }
    attributes_ready = 1;
    result = posix_spawnattr_getflags(&attributes, &flags);
    if (result != 0) {
        goto cleanup;
    }
    flags = (short)(flags | POSIX_SPAWN_CLOEXEC_DEFAULT);
    result = posix_spawnattr_setflags(&attributes, flags);
    if (result != 0) {
        goto cleanup;
    }

    result = posix_spawn(child_pid, executable_path, &actions, &attributes, argv, envp);

cleanup:
    if (attributes_ready) {
        int destroy_result = posix_spawnattr_destroy(&attributes);
        if (result == 0 && destroy_result != 0) {
            result = destroy_result;
        }
    }
    if (actions_ready) {
        int destroy_result = posix_spawn_file_actions_destroy(&actions);
        if (result == 0 && destroy_result != 0) {
            result = destroy_result;
        }
    }
    for (index = 0; index < LOOP_A_FD_COUNT; ++index) {
        if (normalized[index] >= 0) {
            (void)close(normalized[index]);
        }
    }
    if (result != 0) {
        *child_pid = (pid_t)-1;
    }
    return result;
}
