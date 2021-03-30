/*
 * This program gets the number of WRs that a given player (argv[1]) has set.
 * Optionally, a game (argv[2]) can be specified.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "srcom/utils.h"
#include "srcom/worldrecords.h"

void usage(void)
{
	fputs("Usage: `+worldrecords [PLAYER NAME] [GAME (OPTIONAL)]`\n"
	      "Example: `+worldrecords AnInternetTroll mkw`\n",
	      stderr);
	exit(EXIT_FAILURE);
}

int main(int argc, char **argv)
{
	if (argc == 1)
		usage();

	char *uid = get_uid(argv[1]);
	if (!uid) {
		fprintf(stderr, "Error: User with username '%s' not found.\n",
		        argv[1]);
		return EXIT_FAILURE;
	}

	char uri[URIBUF], gid[UIDBUF] = {0}, gname[BUFSIZ];
	if (argc > 2) {
		/* Get the games ID and name. */
		string_t game;
		init_string(&game);
		snprintf(uri, URIBUF, API "/games?abbreviation=%s", argv[2]);
		get_req(uri, &game);

		sscanf(game.ptr,
		       "{\"data\":[{\"id\":\"%[^\"]\",\"names\":{"
		       "\"international\":\"%["
		       "^\"]",
		       gid, gname);

		if (*gid == '\0') {
			fprintf(stderr,
			        "Error: Game with abbreviation '%s' not "
			        "found.\n",
			        argv[2]);
			return EXIT_FAILURE;
		}
	}

	string_t runs;
	init_string(&runs);

	/* Get players PRs. */
	snprintf(uri, URIBUF, API "/users/%s/personal-bests?top=1&game=%s", uid,
	         gid);
	get_req(uri, &runs);

	/*
	 * Each run will have a level. If the level is null, the run is a
	 * fullgame run. Counting the number of "levels" is a quick and easy way
	 * to get the number of runs without the need of parsing the JSON.
	 */
	const unsigned int total = count_substr(runs.ptr,
	                                        "\"level\":", TOTAL_KEY_LEN);
	const unsigned int fullgame = count_substr(runs.ptr, "\"level\":null",
	                                           LEVEL_KEY_LEN);

	if (argc >= 3)
		printf("World Record Count: %s - %s\n", argv[1], gname);
	else
		printf("World Record Count: %s\n", argv[1]);

	printf("Full Game: %u\n"
	       "Individual Level: %u\n"
	       "Total: %u\n",
	       fullgame, total - fullgame, total);
	return EXIT_SUCCESS;
}
