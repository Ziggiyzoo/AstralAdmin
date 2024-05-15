"""
All User Slash Commands for Astral Admin
"""
import random
import string
import discord

from discord.ext import commands

from src.logic import firebase_db_connection, rsi_lookup, update_user_roles

class SlashCommands(commands.Cog):
    """
    Astral Admin Bot Slash Cogs
    """

    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.slash_command(
        name="ping", description="Ping! :)"
      )
    async def ping(self, ctx):
        """
        Ping! :)
        """
        await ctx.respond("Pong!", ephemeral=True)

    # pylint: disable=no-member
    @commands.slash_command(
        name="bind-rsi-account", description="Bind your Discord and RSI Accounts"
    )
    async def bind_rsi_account(self, ctx, rsi_handle: discord.Option(str)):
        """
        Command to start the process of binding Discord & RSI Accounts
        """
        author_name: str = ctx.author.name
        author_id: int = ctx.author.id
        guild_id: int = ctx.guild.id

        await ctx.defer(ephemeral=True)

        if rsi_handle is None:
            await ctx.followup.send(
                "Please input your RSI Handle."
            )
        user =  await rsi_lookup.get_user_info(rsi_handle=rsi_handle)
        if user is None:
            await ctx.followup.send(
                "That RSI Handle is invalid. Please imput a correct Value"
            )
        else:
            # Check if the user exists
            user_info = await firebase_db_connection.get_user(author_id=author_id)
            if user_info is None:
                # They did not exist. Create them.
                code = "".join([random.choice(string.ascii_letters) for n in range(10)])
                await firebase_db_connection.put_new_user(
                    author_id=str(author_id),
                    guild_id=str(guild_id),
                    rsi_handle=user["data"]["profile"]["handle"],
                    display_name=user["data"]["profile"]["display"],
                    user_verification_code=code
                )

                # Tell then user to put the code in their RSI Bio
                await ctx.followup.send(
                    f"Greetings {author_name}" +
                    f", please add the following to your RSI Account's Short Bio: {code}" +
                    "\nThis can be found here: https://robertsspaceindustries.com/account/profile" +
                    "\n\nAfter you have done this please re run this command."
                )

                # Update the user verification step to 1
                await firebase_db_connection.update_user_verification_status(author_id=author_id,
                                                                             user_verification_status=False,
                                                                             user_verification_progress=1)

            else:
                if user_info["user_verification_progress"] == 0:
                    if user_info["user_verification_code"] is not None:
                        await firebase_db_connection.update_user_verification_status(author_id=author_id,
                                                                                     user_verification_status=False,
                                                                                     user_verification_progress=1)
                    else:
                        ctx.followup.send(
                            "There has been an error. Please contact a server Admin."
                        )

                if user_info["user_verification_progress"] == 1:
                    # The user has begun the process and needs verification
                    if await rsi_lookup.verify_rsi_handle(rsi_handle=user_info["user_rsi_handle"],
                                                          verification_code=user_info["user_verification_code"]):
                        await firebase_db_connection.update_user_verification_status(author_id=author_id,
                                                                                     user_verification_progress=2,
                                                                                     user_verification_status=True)
                        await firebase_db_connection.update_user_guild_verification(author_id=author_id,
                                                                                    guild_id=guild_id,
                                                                                    guild_verification_status=True)
                        user_list = []
                        user_list.append(user_info)
                        await update_user_roles.update_user_roles(self, user_list=user_list, bot=self.bot, ctx=ctx)
                        await ctx.followup.send(
                            f"Thank you {rsi_handle}, your Discord and RSI Accounts are now symbollically bound."
                            + "\n\nYou will not be able to access any more of the server unless you are a "
                            + "Member or Affiliate of Astral Dynamics.",
                            ephemeral=True
                        )
                        try:
                            await ctx.author.edit(nick=user_info["user_display_name"])
                            await ctx.author.add_role(
                                discord.utils.get(
                                    ctx.guild.roles,
                                    name="Account Bound"
                                )
                            )
                        except discord.errors.Forbidden as exc:
                            print(exc)

                    else:
                        await ctx.followup.send(
                            "Please make sure that you have added your verification code to your RSI Short Bio:" +
                            f"\nVerification Code {user_info['user_verification_code']}" +
                            "\nEdit your RSI Profile here: https://robertsspaceindustries.com/account/profile"
                        )


                if user_info["user_verification_progress"] == 2:
                    await ctx.followup.send(
                        "You have already bound your Discord and RSI Accounts!" +
                        "\nIf you haven't already, sign up for a position at Astral Dynamics!" +
                        "\nhttps://robertsspaceindustries.com/orgs/ASTDYN"
                    )

    @commands.slash_command(
            name="apply-now", description="Assistance with applying to the Astral Dynamics Organistation."
    )
    async def apply_now(self, ctx):
        """
        Send the user instructions on how to apply to Astral Dynamics.
        """
        ctx.respond("Hi there " + ctx.author_id + ". To Apply to Astral Dynamics please use this link:"
                    + "\n\nhttps://robertsspaceindustries.com/orgs/ASTDYN"
                    + "\n\nOnce you have done this please @ mention Human Resources.",
                    ephemeral=True)

    # pylint: disable=no-member
    @commands.slash_command(
        name="add-guild", description="Add the Discord Guild to the DB."
    )
    @commands.has_permissions(administrator=True)
    async def add_guild(self, ctx, spectrum_id: discord.Option(str)):
        """
        Admin only command to add the guild to the DB
        """
        if await firebase_db_connection.put_new_guild(
            str(ctx.guild_id), ctx.guild.name, spectrum_id
            ):
            await ctx.respond("This Discord server has been added to the Database.",
                              ephemeral=True)
        else:
            await ctx.respond("The Discord server failed to be added to the Database",
                              ephemeral=True)

    @commands.slash_command(
            name="del-guild", description="Delete the Discord Guild from the DB."
    )
    @commands.has_permissions(administrator=True)
    async def del_guild(self, ctx):
        """
        Admin only command to delete the Discord Guild from the DB
        """
        if await firebase_db_connection.del_guild(guild_id=str(ctx.guild_id)):
            await ctx.respond("The Discord server has been removed from the Database",
                                ephemeral=True)
        else:
            ctx.respond("The Discord server failed to be removed from the Database",
                        ephemeral=True)

    @commands.slash_command(
    name="update-roles", description="Update the roles of bound members on the discord."
    )
    @commands.has_permissions(administrator=True)
    async def update_org_roles(self, ctx):
        """
        Admin only command to trigger the update of Discord roles based of the RSI Org page.
        """
        await ctx.respond("Running roles Update Now")
        info = self.bot.get_channel(1233738280118390795)
        guild_ids = await firebase_db_connection.get_guild_ids()
        for guild_id in guild_ids:
            # Get list of verified members in the guild
            guild_members = await firebase_db_connection.get_guild_members(guild_id=guild_id)

            # Get verified member info
            user_list = []
            try:
                for member_id in guild_members:
                    user_list.append(
                        await firebase_db_connection.get_user(author_id=str(member_id))
                    )
            except Exception as exc:
                print("FAILED CREATING USER LIST: " + str(exc))

            response = await update_user_roles.update_user_roles(user_list=user_list, bot=self.bot, guild_id=guild_id)
            await info.send(response)

def setup(bot):
    """
    Add Cog to Bot
    """
    try:
        bot.add_cog(SlashCommands(bot))
        print("Slash Commands Cog Added")
    except Exception as exc:
        print(exc)
  
